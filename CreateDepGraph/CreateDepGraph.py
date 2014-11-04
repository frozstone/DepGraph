from xml.dom import minidom
from os import listdir, path

#Properties
xhtmlDir = ''
tagsWithBase = ['mroot', 'msub', 'msup', 'msubsup', 'munder', 'mover', 'munderover', 'mmultiscripts', ] #consider mstyle

def __getXHTMLFiles(sourceDir):
    return [path.join(sourceDir, flName) for flName in listdir(sourceDir)]

def __expandMath(mt):
    '''
        mt : xml element
        return value : list of xml elements
    '''
    retval = [mt]
    for tag in tagsWithBase:
        children = mt.getElementsByTagName(tag)
        if len(children) > 0:
            for child in children:
                retval.append(child.firstChild)
    return retval

def __expandMaths(mts):
    '''
        mts : {idx:<math>}
    '''
    for idx, mt in mts.iteritems():
        mts[idx] = __expandMath(mt)

if __name__ == '__main__':
    files = __getXHTMLFiles()
    for fl in files:
        xdoc = minidom.parse(fl)
        
        #enumerate if there is no id in the <math> tag
        mts = {idx:mt for idx,mt in enumerate(xdoc.getElementsByTagName('math'))}