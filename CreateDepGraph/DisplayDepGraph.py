from os import listdir, path
from xml.dom import minidom
import shutil
import random as rd
import networkx as nx

#Properties
n = 10 #number of random papers
destSamplePapers = '/home/giovanni/paperssample/'
dirs = ['/works/csisv16/giovanni/ntcir11/harasan/xml_newdep/3/', '/works/csisv16/giovanni/ntcir11/harasan/xml_newdep/4/', '/works/csisv16/giovanni/ntcir11/harasan/xml_newdep/5/', '/works/csisv11/giovanni/harasan/xml_newdep/6/', '/works/csisv11/giovanni/harasan/xml_newdep/7/', '/works/csisv12/giovanni/harasan/xml_newdep/8/', '/works/csisv12/giovanni/harasan/xml_newdep/9/', '/works/csisv12/giovanni/harasan/xml_newdep/11/']

def __getAllPapers():
    papers = []
    for d in dirs:
        papers.extend(path.join(d, p) for p in listdir(d))
    return papers

def __checkLatexExistence(fl):
    xdoc = minidom.parse(fl)
    exps = xdoc.getElementsByTagName('expression')
    if len(exps) > 200:
        return False

    for exp in exps:
        annLatex = [ann for ann in exp.firstChild.firstChild.getElementsByTagName('annotation') if ann.hasAttribute('encoding') and ann.getAttribute('encoding') == 'application/x-tex']
        if not (exp.firstChild.firstChild.hasAttribute('alttext') or len(annLatex) > 0):
            return False
    return True

def __getRandomPapers(allpapers):
    papers = set([])
    count = 0
    while count < n:
        temppaper = rd.sample(allpapers, 1)[0]
        if __checkLatexExistence(temppaper):
            papers.add(temppaper)
            count += 1
            print temppaper, count
    return papers

def __populatePapers(papers):
    for p in papers:
        shutil.copyfile(p, path.join(destSamplePapers, path.basename(p)))

if __name__ == '__main__':
    #populate the papers (xml) randomly --> 10?
    #check the ones where all exp has latex annotation or alttex
    #draw depgraph from them
    allpapers = __getAllPapers()
    rdpapers = __getRandomPapers(allpapers)
    __populatePapers(rdpapers)
