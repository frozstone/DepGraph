from xml.dom import minidom
from os import listdir, path
import re
from sys import argv

#Properties
xmlDir = 'vartab/xml/'
sentenceDir = 'vartab/multifiles/'
tagsWithBase = ['mroot', 'msub', 'msup', 'msubsup', 'munder', 'mover', 'munderover', 'mmultiscripts'] #have not considered mstyle
re_baseTags = '<(tags)>((?!(tags)>).)*</(tags)>'
re_mathSymbol = '__MATH_\d+__'
expressiontag = 'expression'
mathtag = 'math'
pageDestDir = 'vartab/xml_newdep/'

def enum(**enums):
    return type('Enum', (object,), enums)
 
LinkType = enum(comp=1, simcomp=2, exp=3, simexp=4)

def __printLinkType(ltype):
    if ltype == LinkType.comp:
        return "comp"
    elif ltype == LinkType.simcomp:
        return "similarcomp"
    elif ltype == LinkType.exp:
        return "sameexpression"
    elif ltype == LinkType.simexp:
        return "similarexpression"

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

def __removeAnnotation(mt):
    '''
        mt: an xml element
    '''
    pointer = mt.getElementsByTagName('semantics')
    if len(pointer) > 0 and pointer[0].firstChild != None:
        temp = pointer[0].firstChild
        #remove attributes of res
        return mt.firstChild.getAttribute('id'), __removeUnreqTags(__removeAttributes(temp).toxml())
    else:
        return mt.firstChild.getAttribute('id'), ''

def __removeUnreqTags(mts_string):
    '''
    call this procedure only after removing the attributes in tags
    '''
    return mts_string.replace('<mstyle>', '').replace('<mstyle>', '').replace('<mstyle />', '')


def __checkIfTwoMathsAreConnected(math1, math2):
    '''
        math1, math2 : lists of candidate matchers
        return True if an edge should be drawn from math1 to math2
    '''
    for idx1, mt1 in enumerate(math1):
        for idx2, mt2 in enumerate(math2):
            if mt2 != '' and (mt2 in mt1 or mt2.lower() in mt1.lower()) and mt1 != mt2:

                if idx1 == 0 and idx2 == 0 and mt2 in mt1 and math2[-1] == math1[-1]:
                    return True, LinkType.exp
                elif idx1 == 0 and idx2 == 0 and mt2 in mt1 and math2[-1] != math1[-1]:
                    return True, LinkType.comp
                elif math2[-1] == math1[-1]:
                    return True, LinkType.simexp
                else:
                    return True, LinkType.simcomp
    return False, None

def __createEdges(mts, uniquegmids, gumidmappings):
    '''
        mts: {gmid:[matchers]} --> unique mts
        output: edge --> {gumidparent:(gumidchild, linktype)}
    '''
    edges = {}
    for gmid1 in uniquegmids:
        matchers1 = mts[gmid1]
        for gmid2 in uniquegmids:
            matchers2 = mts[gmid2]
            if gmid1 == gmid2:
                continue
            isConn, link = __checkIfTwoMathsAreConnected(matchers1, matchers2)
            if isConn and gumidmappings[gmid1] in edges:
                    edges[gumidmappings[gmid1]].append((gumidmappings[gmid2], link))
            elif isConn:
                    edges[gumidmappings[gmid1]] = [(gumidmappings[gmid2], link)]
    return edges

def __getGmidMappings(gumidmappings):
    gmidmappings = {}
    for k,v in gumidmappings.iteritems():
        if v in gmidmappings:
            gmidmappings[v].append(k)
        else:
            gmidmappings[v] = [k]
    return gmidmappings

def __getUniqueMaths(mts):
    '''
        mts : {'gmid': [mathml in string]}
    '''
    uniquemts = {} #--> {mathml in string:gumid}
    uniquegmids = []
    gumidmapping = {}
    for gmid, v in mts.iteritems():
        if v[0] in uniquemts:
            gumidmapping[gmid] = uniquemts[v[0]]
        else:
            gumid = gmid[:gmid.rindex('#') + 1] + 'u' + str(len(uniquemts))
            gumidmapping[gmid] = gumid
            uniquemts[v[0]] = gumid
            uniquegmids.append(gmid)
    return uniquegmids, gumidmapping, __getGmidMappings(gumidmapping)

def __getSummary(gmidmappings, descriptions):
    '''
    input:  gmidmappings --> {gumid:[gmid1, gmid2]}
            descriptions --> {gmid:[desc1, desc2]}
    output: summaries --> {gumid: summary}
    '''
    summaries = {} #--> {gumid: summary}
    for gumid, gmids in gmidmappings.iteritems():
        descs = {gmid:descriptions[gmid] for gmid in gmids}
        orddescs = sorted(descs.items(), key=lambda k: (int(k[0][k[0].rindex('_') + 1:k[0].rindex('.xhtml')]), int(k[0][k[0].rindex('#') + 1:]))) #--> key: (paraid, mid)
        for orddesc in orddescs:
            if len(orddesc[1]) > 0:
                #get the longest description
                summaries[gumid] = sorted(orddesc[1], key=lambda k: len(k), reverse=True)[0]
    return summaries

def __getDepGraphAndComponents(xdoc):
    '''
        output: 
            1. edges: {gumid1:[(gumid2, linktype)]} --> component list
            2. gumidmappings: {gmid:gumid}
    '''
        
    #enumerate if there is no id in the <math> tag
    rawmts = {}
    mts = {}
    mts_conventional = {}
        
    #for xhtml, enumerate mathtag; for xml, enumerate expressiontag
    for idx, exp in enumerate(xdoc.getElementsByTagName(expressiontag)):
        gmid = exp.getAttribute('gmid')
        mt = exp.getElementsByTagName(mathtag)[0]
        rawmts[gmid] = mt

        initial = __normalizeMathTags(mt.toxml())
        mid, formattedmath = __removeAnnotation(minidom.parseString(initial.encode('utf-8')))
        expanded =__expandMaths(formattedmath)
        mts_conventional[gmid] = [__getValueOfMathTags(formattedmath)]
        mts[gmid] = expanded
    
    uniquegmids, gumidmappings, gmidmappings = __getUniqueMaths(mts_conventional)
    edges = __createEdges(mts, uniquegmids, gumidmappings)

    components = {} #{gumid: [comp1, comp2]}
    for exp in xdoc.getElementsByTagName(expressiontag):
        gmid = exp.getAttribute('gmid')
        #get components
        if gumidmappings[gmid] in edges:
            components[gumidmappings[gmid]] = edges[gumidmappings[gmid]]

    return rawmts, gmidmappings, gumidmappings, components

def __handleMathInText(txt, gmid, dictmath):
    #1. replace the __MATH_*__
    #2. set the value of the 'text' attribute
    mathsymbols = re.findall(re_mathSymbol, txt)
    textAtt = txt.replace('&', '&amp;').replace('"', '&quot;').replace("'", '&apos;').replace('<', '&lt;').replace('>', '&gt;')
    textVal = textAtt
    for mathsymbol in mathsymbols:
        gpid = gmid[:gmid.rindex('#')]
        mid = mathsymbol[7:mathsymbol.rindex('__')]
        idx = gpid + '#' + mid
        textAtt = textAtt.replace(mathsymbol, '')
        textVal = textVal.replace(mathsymbol, dictmath[idx].toxml().encode('utf-8'))

    return textVal, textAtt

def __processDescriptions(ele, dictmath):
    '''
        descs: list of <description>
        TODO:   1. decide which descriptions will be displayed (attribute display="0 or 1")
                2. replace the __MATH_*_ to its mathml representation
                3. set the value of the 'text attribute'
    '''
    gmid = ele.getAttribute('gmid')
    descs = ele.getElementsByTagName('description')
    uniqueDescs = []
    #1. decide which descriptions will be displayed (attribute display="0 or 1")
    #   -->find the unique and longest descriptions
    for idx1, desc1 in enumerate(descs):
        if desc1.hasAttribute('type') or desc1.firstChild is None:
            continue
        isUnique = True
        norm_desc1 = desc1.firstChild.nodeValue.lower()
        for idx2, desc2 in enumerate(descs):
            if idx1 == idx2 or desc2.hasAttribute('type') or desc2.firstChild is None:
                continue
            norm_desc2 = desc2.firstChild.nodeValue.lower()
            if norm_desc1 in norm_desc2 or any(norm_desc1 == uDesc for uDesc in uniqueDescs):
                isUnique = False
                break

        descVal, descAtt = __handleMathInText(desc1.firstChild.nodeValue, gmid, dictmath)
        descs[idx1].setAttribute('text', descAtt)
        descs[idx1].firstChild.replaceWholeText(descVal)
        if isUnique:
            descs[idx1].setAttribute('display', '1')
            uniqueDescs.append(norm_desc1)
        else:
            descs[idx1].setAttribute('display', '0')

def __getSentencesForMathPapers(fl):
    '''
    Input: papername, e.g., vartabl/xml/astro-ph990480.xml
    Ouput: {para#kmcs-r id:'sentence'}, e.g. {ph9912005_1_3.xhtml#0:'test'}
    '''
    mathSentences = {}
    paperDir = fl.replace(xmlDir, sentenceDir).replace('.xml', '')
    paras = listdir(paperDir)
    for para in paras:
        paraname = para.replace('.txt', '.xhtml')
        lines = open(path.join(paperDir, para))
        for line in lines:
            maths = re.findall(re_mathSymbol, line.strip())
            for math in maths:
                mathSentences[paraname + '#' + math[7:math.rindex('__')]] = line.strip()
    return mathSentences

def __createXML(fl):
    '''
    Info: 
    - current description tags contain description from its own, other appearances of that expression, or from the old component
    - the new description tags will be the same as the previous ones. However, the components will be revised, ene though the description from new component will not be added to the description tags.
    TODO:
        1. Preprocess the description tags which contain its own desc
        
    '''
    xdoc = minidom.parse(fl)
    #sentences = __getSentencesForMathPapers(fl[fl.rindex('/') + 1:fl.rindex('.xml')])
    sentences = __getSentencesForMathPapers(fl)
    rawmts, gmidmappings, gumidmappings, components = __getDepGraphAndComponents(xdoc)

    descriptions = {}
    
    for exp in xdoc.getElementsByTagName(expressiontag):
        gmid = exp.getAttribute('gmid')
        descEles = [desc for desc in exp.getElementsByTagName('description') if not desc.hasAttribute('type') and desc.firstChild is not None]
        descriptions[gmid] = [ele.firstChild.nodeValue for ele in descEles]
    
    summaries = __getSummary(gmidmappings, descriptions)
    for exp in xdoc.getElementsByTagName(expressiontag):
        gmid = exp.getAttribute('gmid')

        #add gumid
        exp.setAttribute('gumid', gumidmappings[gmid])

        #add sentences ele
        sentVal, sentAtt = __handleMathInText(sentences[gmid[gmid.rindex('/') + 1:]], gmid, rawmts)
        sentxml = minidom.parseString('<sentence text="' + sentAtt + '">' + sentVal + '</sentence>')
        exp.appendChild(sentxml.firstChild)

        #add component eles
        if gumidmappings[gmid] in components:
            for component in components[gumidmappings[gmid]]:
                compxml = minidom.parseString('<component gumid="' + component[0] + '" type="' + __printLinkType(component[1]) + '" />')
                exp.appendChild(compxml.firstChild)

        __processDescriptions(exp, rawmts)
        
        #remove old summary
        for summ in exp.getElementsByTagName('summary'):
            exp.removeChild(summ)
        #add summary ele
        if gumidmappings[gmid] in summaries and summaries[gumidmappings[gmid]].strip() != '':
            smrVal, smrAtt = __handleMathInText(summaries[gumidmappings[gmid]], gmid, rawmts)
            smrxml = minidom.parseString('<summary text="' + smrAtt.encode('utf-8') + '">' + smrVal.encode('utf-8') + '</summary>')
            exp.appendChild(smrxml.firstChild)

    f = open(fl.replace(xmlDir, pageDestDir), 'w')
    f.write(xdoc.toxml('utf-8'))
    f.close()
    

def MainMethodForTest():
    files = __getFiles(xmlDir, '.xml')
    for fl in files:
        __createXML(fl)
    return True

if __name__ == '__main__':
    #Preparation
    __generateRegex()
    #__createXML(fl)
    try:
        MainMethodForTest()
    except:
        print 'error'
    print 'finish'