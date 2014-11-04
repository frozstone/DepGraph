from xml.dom import minidom
from os import listdir, path

#Properties
xhtmlDir = 'D:/Virtual/vartab/'
tagsWithBase = ['mroot', 'msub', 'msup', 'msubsup', 'munder', 'mover', 'munderover', 'mmultiscripts', ] #consider mstyle
mathtag = 'm:math'

def __getXHTMLFiles(sourceDir):
    return [path.join(sourceDir, flName) for flName in listdir(sourceDir) if flName.endswith('xhtml')]

def __expandMaths(mts):
    '''
        mts : {idx:<math>}
    '''
    def __expandMath(mt):
        '''
            mt : xml element
            return value : list of xml elements
            algorithms: do not use only the base for each tag, but instead combine it with the rest
        '''
        retval = [mt]
        for tag in tagsWithBase:
            children = mt.getElementsByTagName(tag)
            if len(children) > 0:
                for child in children:
                    retval.append(child.firstChild)
        return retval

    for idx, mt in mts.iteritems():
        __removeAttributes(mt)
        mts[idx] = __expandMath(mt)

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


def __createDepGraph(mts):
    '''
        mts: {idx:[matchers]}
    '''
    edges = []
    for idx, matchers in mts.iteritems():
        for idx2, matchers2 in mts.iteritems():


if __name__ == '__main__':
    files = __getXHTMLFiles(xhtmlDir)
    for fl in files:
        xdoc = minidom.parse(fl)
        
        #enumerate if there is no id in the <math> tag
        mts = {idx:mt for idx,mt in enumerate(xdoc.getElementsByTagName(mathtag))}
        __expandMaths(mts)