from xml.dom import minidom
from os import listdir, path
import re
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

#Properties
tagsWithBase = ['mroot', 'msub', 'msup', 'msubsup', 'munder', 'mover', 'munderover', 'mmultiscripts'] #have not considered mstyle
re_baseTags = '<(tags)>((?!(tags)>).)*</(tags)>'
mathtag = 'math'

#Properties for evaluation
#PLEASE CONSIDER UNIQUE MATH INSTEAD
descDir = 'D:/ntcir10/annotation/test/' #do for annotation and extraction data
mathDir = 'D:/ntcir10math/'
webDestDir = 'D:/vartab/xhtmleval/'
stopwds = set(stopwords.words('english'))
st = PorterStemmer()

def __generateRegex():
    tags = '|'.join(tagsWithBase)
    global re_baseTags
    re_baseTags = re_baseTags.replace('tags', tags)
    return True

def __getFiles(sourceDir, extension):
    return [path.join(sourceDir, flName) for flName in listdir(sourceDir) if flName.endswith(extension)]

def __expandMaths(mts_string):
    '''
        mts : {idx:'<math>'}
        Remember to remove the <math> tags
    '''
    result = re.search(re_baseTags, mts_string)
    if result is None:
        #no new matcher candidate
        return [__getValueOfMathTags(mts_string)]
    nonbase = minidom.parseString(mts_string[result.start():result.end()].encode('utf-8'))
    base = nonbase.firstChild.firstChild.toxml()
    new_mts = mts_string[:result.start()] + base + mts_string[result.end():]
    return [__getValueOfMathTags(mts_string)] + __expandMaths(new_mts)

def __getValueOfMathTags(mts_string):
    return mts_string.replace('<math>', '').replace('</math>', '')

def __normalizeMathTags(mts_string):
    return mts_string.replace('<m:', '<').replace('</m:', '</')

def __removeAnnotation(mt):
    '''
        mt: an xml element
    '''
    pointer = mt.getElementsByTagName('semantics')
    if len(pointer) > 0 and pointer[0].firstChild != None:
        temp = pointer[0].firstChild
        #remove attributes of res
        return mt.firstChild.getAttribute('id'), __removeAttributes(temp).toxml()
    else:
        return mt.firstChild.getAttribute('id'), ''

def __removeAttributes(mt):
    '''
        mt: an xml element
    '''
    if mt.attributes:
        for key in mt.attributes.keys():
            mt.removeAttribute(key)
    for node in mt.childNodes:
        __removeAttributes(node)
    return mt

#Methods for evaluation
def __checkIfTwoMathsAreSameBase(math1, math2):
    '''
        math1, math2 : lists of candidate matchers
        return True if an edge should be drawn from math1 to math2
    '''
    for mt1 in math1:
        for mt2 in math2:
            if mt2 == mt1:
                return True
    return False

def __createDepGraphForEval(mts, type):
    '''
        mts: {idx:[matchers]}
        type: old or new
    '''
    edges = {}
    for idx1, matchers1 in mts.iteritems():
        for idx2, matchers2 in mts.iteritems():
            if idx1 != idx2 and __checkIfTwoMathsAreSameBase(matchers1, matchers2):
                if type == 'new' or (type == 'old' and matchers2[0] in matchers1[0]):
                    if idx1 not in edges:
                        edges[idx1] = [idx2]
                    else:
                        edges[idx1].append(idx2)
    return edges

def __groupParasBasedOnPaper(paras):
    papers = {}
    for para in paras:
        paper = para[para.rindex('/') + 1:para.rindex('_')]
        if paper not in papers:
            papers[paper] = [para]
        else:
            papers[paper].append(para)
    return papers

def __textualizeDescription(ranges, tokens):
    clean_ranges = ranges.replace('[','').replace(']','')
    regions = clean_ranges.split(',')

    texts = ''
    for region in regions:
        if '-' in region:
            startidx = int(region.split('-')[0])
            endidx = int(region.split('-')[1])
            texts +=  ' ' + ' '.join(tokens[idx] for idx in range(startidx, endidx + 1))
        else:
            idx = int(region)
            texts += ' ' + tokens[idx]
    return texts.strip()

def __getDescriptionFromPara(fl):
    '''
        fl represent para
    '''
    lns = open(fl).readlines()
    tokens = {}
    desc = {}
    desc_text = {}

    papername = fl[fl.rindex('/') + 1:fl.rindex('_')]
    mt = ''
    for ln in lns:
        if ln.strip() != '' and str.isdigit(ln.strip()[0]):
            cells = ln.strip().split('\t')
            tokens[int(cells[0])] = cells[1]
        elif ln.startswith('MATH_'):
            mt = ln.strip().replace('_', '_' +papername + '_')
        elif ln.startswith('['):
            if mt in desc:
                desc[mt].append(ln.strip())
                desc_text[mt].append(__textualizeDescription(ln.strip(), tokens))
            else:
                desc[mt] = [ln.strip()]
                desc_text[mt] = [__textualizeDescription(ln.strip(), tokens)]
    return desc, desc_text

def __getDescriptionFromParas(fls):
    '''
        fls represent paras
    '''
    descs = {}
    descs_text = {}
    for fl in fls:
        desc, desc_text = __getDescriptionFromPara(fl)
        descs.update(desc)
        descs_text.update(desc_text)
    return descs, descs_text

def __getDepGraphForEval(fl, mathInDescFiles):
    '''
        NOTE:   The math tags for evaluation are obtained using math understanding dataset.
                They use xmlns --> <m:math>
        Return: edges_conventional and edges
                edges = {idx1:[mt1, mt2, ...]}
    '''
    lns = open(fl).readlines()

    mts = {}
    mts_conventional = {}

    nmaths = 0
    nuniquemaths = 0
    for ln in lns:
        cells = ln.strip().split('\t')
        if ln.strip() == '' and not cells[0] in mathInDescFiles:
            continue

        nmaths += 1 #if ln.startswith('MATH_') else 0
        
        initial = __normalizeMathTags(cells[1])
        mid, formattedmath = __removeAnnotation(minidom.parseString(initial))
        expanded = __expandMaths(formattedmath)
        mts_conventional[cells[0]] = [__getValueOfMathTags(formattedmath)]
        mts[cells[0]] = expanded

    edges_conventional = __createDepGraphForEval(mts, 'old')
    edges = __createDepGraphForEval(mts, 'new')
    uniquemaths = __getUniqueMaths(mts_conventional)
    return edges_conventional, edges, nmaths, mts_conventional, uniquemaths

def __getNumberOfMathsHavingDesc(descs, mathml, edges=None):
    mts = []
    for mt, desc in descs.iteritems():
        mts.append(mt)
        if edges is not None and mt in edges:
            mts.extend(edges[mt])

    allmaths = list(set(mts))
    for i, mt in enumerate(allmaths):
        allmaths[i] = mathml[mt][0]
    return list(set(mts)), list(set(allmaths))

def __getUniqueMaths(mts):
    '''
        mts : {'id': [mathml in string]}
    '''
    uniquemts = {}

    for k, v in mts.iteritems():
        if v[0] in uniquemts:
            uniquemts[v[0]].append(k)
        else:
            uniquemts[v[0]] = [k]
    return uniquemts

def __getDiffDescs(edgesOld, edgesNew, dictmath, descs_text):
    eold = [(k,val) for k,v in edgesOld.iteritems() for val in v]
    enew = [(k,val) for k,v in edgesNew.iteritems() for val in v]
    ediff = list(set(enew).difference(set(eold)))
    uniquemathml = set()
    ediffdict = {}

    for e in ediff:
        if dictmath[e[0]][0] in uniquemathml:
            continue
        else:
            uniquemathml.add(dictmath[e[0]][0])

        if e[0] in ediffdict:
            ediffdict[e[0]].append(e[1])
        else:
            ediffdict[e[0]] = [e[1]]
    return ediffdict

def __customizeHtmlColor(parentdesc, childdesc, usedtokens):
    parenttokens = [st.stem(token).lower() for token in parentdesc.split(' ')]
    childtokens = childdesc.split(' ')
    retval = []
    for token in childtokens:
        normalizedtoken = st.stem(token).lower()
        if normalizedtoken not in usedtokens and normalizedtoken not in parenttokens and normalizedtoken not in stopwds:
            retval.append('<font color="Red">' + token + '</font>')
            usedtokens.add(normalizedtoken)
        else:
            retval.append(token)
    return ' '.join(retval)

def __showEvalDescAsWebPage(edges, flname, dictmath, uniquemaths, dictdesc, destflname):
    page = []
    page.append('<html xmlns="http://www.w3.org/1999/xhtml"><meta charset="UTF-8" /><body>\n')
    page.append('<h2>' + flname + '</h2><br/>\n')
    for parentid, children in edges.iteritems():
        usedtokens = set()

        parentdesclist = []
        for mid in uniquemaths[dictmath[parentid][0]]:
            if mid in dictdesc:
                parentdesclist.extend(dictdesc[mid])

        parentdescs = ' ; '.join(parentdesclist) if len(parentdesclist) > 0 else ''
        parentdescs_normalized = __customizeHtmlColor('', parentdescs, usedtokens)
        page.append('<font size="6" color="Red"><math>' + dictmath[parentid][0].encode('utf-8') + '</math></font>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<font size="4">' + parentdescs_normalized + '</font><br/>\n')
        
        for childid in children:
            childdesclist = []
            for mid in uniquemaths[dictmath[childid][0]]:
                if mid in dictdesc:
                    childdesclist.extend(dictdesc[mid])

            childdescs = ' ; '.join(childdesclist) if len(childdesclist) > 0 else ''
            childdescs_normalized = __customizeHtmlColor(parentdescs, childdescs, usedtokens)
            page.append('<font size="4"><math>' + dictmath[childid][0].encode('utf-8') + '</math></font>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<font size="4">' + childdescs_normalized + '</font><br/>\n')
        page.append('<br/><br/>\n')

    page.append('</body></html>')
    f = open(destflname, 'w')
    f.writelines(page)
    f.close()

def MainMethodForEval():
    descFiles = __getFiles(descDir, '.txt')
    nmaths = 0
    nmaths_desc_wo_dep = 0
    nmaths_desc_olddep = 0
    nmaths_desc_newdep = 0

    nuniquemaths = 0
    nunique_desc_nodep = 0
    nunique_desc_olddep = 0
    nunique_desc_newdep = 0

    edges_olddep = 0
    edges_newdep = 0
    papers = __groupParasBasedOnPaper(descFiles)
    for p in papers.keys():
        #if p != '0801.2412':
        #    continue
        descs, descs_text = __getDescriptionFromParas(papers[p])
        edgesConv, edgesNew, nmts, mts, uniquemts = __getDepGraphForEval(path.join(mathDir, p) + '_output.txt', descs.keys())

        mts_desc_nodep, unique_mts_nodep = __getNumberOfMathsHavingDesc(descs, mts)
        mts_desc_olddep, unique_mts_olddep = __getNumberOfMathsHavingDesc(descs, mts, edgesConv)
        mts_desc_newdep, unique_mts_newdep = __getNumberOfMathsHavingDesc(descs, mts, edgesNew)

        nmaths += nmts
        nmaths_desc_wo_dep += len(mts_desc_nodep)
        nmaths_desc_olddep += len(mts_desc_olddep)
        nmaths_desc_newdep += len(mts_desc_newdep)
        
        nuniquemaths += len(uniquemts)
        nunique_desc_nodep += len(unique_mts_nodep)
        nunique_desc_olddep += len(unique_mts_olddep)
        nunique_desc_newdep += len(unique_mts_newdep)

        edges_olddep += sum(len(v) for k, v in edgesConv.iteritems())
        edges_newdep += sum(len(v) for k, v in edgesNew.iteritems())

        ediff = __getDiffDescs(edgesConv, edgesNew, mts, descs_text)
        __showEvalDescAsWebPage(ediff, p, mts, uniquemts, descs_text, path.join(webDestDir, p + '.html'))

    print len(papers)
    print edges_olddep, edges_newdep
    print nmaths, nmaths_desc_wo_dep, nmaths_desc_olddep, nmaths_desc_newdep
    print nuniquemaths, nunique_desc_nodep, nunique_desc_olddep, nunique_desc_newdep
    return True

if __name__ == '__main__':
    #Preparation
    __generateRegex()
    MainMethodForEval()
    print 'finish'
