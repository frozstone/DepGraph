from xml.dom import minidom
from os import listdir, path
import re
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

#Properties
xhtmlDir = 'vartab/'
tagsWithBase = ['mroot', 'msub', 'msup', 'msubsup', 'munder', 'mover', 'munderover', 'mmultiscripts'] #have not considered mstyle
re_baseTags = '<(tags)>((?!(tags)>).)*</(tags)>'
expressiontag = 'expression'
mathtag = 'math'
pageDestDir = 'vartab/xhtml/'

#Properties for evaluation
#PLEASE CONSIDER UNIQUE MATH INSTEAD
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

def __checkIfTwoMathsAreConnected(math1, math2):
    '''
        math1, math2 : lists of candidate matchers
        return True if an edge should be drawn from math1 to math2
    '''
    for mt1 in math1:
        for mt2 in math2:
            if mt2 in mt1:
                return True
    return False

def __createDepGraph(mts):
    '''
        mts: {idx:[matchers]}
    '''
    edges = []
    for idx1, matchers1 in mts.iteritems():
        for idx2, matchers2 in mts.iteritems():
            if idx1 != idx2 and __checkIfTwoMathsAreConnected(matchers1, matchers2):
                edges.append((idx1, idx2))
    return edges

def __getDifferenceBetweenGraphs(edgesConv, edges):
    edgesDiff = []
    for edge in edges:
        if edge not in edgesConv:
            edgesDiff.append(edge)
    return edgesDiff

def __showAsWebPage(edges, flname, dictmath, dictdesc, destflname):
    page = []
    page.append('<html xmlns="http://www.w3.org/1999/xhtml"><meta charset="UTF-8" /><body>\n')
    page.append('<h2>' + flname + '</h2><br/>\n')
    for edge in edges:
        parentid = edge[0]
        childid = edge[1]
        page.append('<math>' + dictmath[parentid][0].encode('utf-8') + '</math>     <font size="4" color="Red">' + dictdesc[parentid].encode('utf-8') + '</font><br/>\n')
        page.append('<math>' + dictmath[childid][0].encode('utf-8') + '</math>     <font size="4" color="Red">' + dictdesc[childid].encode('utf-8') + '</font><br/>\n')
        page.append('<br/><br/>\n')

    page.append('</body></html>')
    f = open(destflname, 'w')
    f.writelines(page)
    f.close()

def __getDepGraphForTest(fl):
    '''
        This method is used only for comparing new dep graph to the previous one.
        Therefore, there is no need to return any meaningful value.
    '''
    xdoc = minidom.parse(fl)
        
    #enumerate if there is no id in the <math> tag
    mts = {}
    mts_conventional = {}
    descriptions = {}
        
    #for xhtml, enumerate mathtag; for xml, enumerate expressiontag
    for idx, exp in enumerate(xdoc.getElementsByTagName(expressiontag)):
        #remove this line when using xhtml
        mt = exp.getElementsByTagName(mathtag)[0]

        initial = __normalizeMathTags(mt.toxml())
        mid, formattedmath = __removeAnnotation(minidom.parseString(initial.encode('utf-8')))
        expanded =__expandMaths(formattedmath)
        mts_conventional[mid] = [__getValueOfMathTags(formattedmath)]
        mts[mid] = expanded

        descriptiontags = [desc.firstChild.nodeValue for desc in exp.getElementsByTagName('description') if not desc.hasAttribute('type') and desc.firstChild is not None]
        descriptions[mid] = descriptiontags[0] if len(descriptiontags) > 0 else ''
        
    edges_conventional = __createDepGraph(mts_conventional)
    edges = __createDepGraph(mts)
    edges_diff = __getDifferenceBetweenGraphs(edges_conventional, edges)
    print len(edges), len(edges_conventional)

    destPath = path.join(pageDestDir, path.basename(fl).replace('.xml', '.html'))
    __showAsWebPage(edges_diff, path.basename(fl), mts, descriptions, destPath)

    return True

def MainMethodForTest():
    files = __getFiles(xhtmlDir, '.xml')
    for fl in files:
        __getDepGraphForTest(fl)
    return True


if __name__ == '__main__':
    #Preparation
    __generateRegex()
    MainMethodForEval()
    print 'finish'