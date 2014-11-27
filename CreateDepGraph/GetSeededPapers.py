from os import listdir, path
from shutil import copyfile

tsvfile = 'MCAT_dep-descriptions.tsv'
scorefile = 'NTCIR11_Math-qrels.dat'
queries = [24,50,28,20,12]
destDir = 'seedxmls/'
dirs = ['/works/csisv16/giovanni/ntcir11/harasan/xml_newdep/3/', '/works/csisv16/giovanni/ntcir11/harasan/xml_newdep/4/', '/works/csisv16/giovanni/ntcir11/harasan/xml_newdep/5/', '/works/csisv11/giovanni/harasan/xml_newdep/6/', '/works/csisv11/giovanni/harasan/xml_newdep/7/', '/works/csisv12/giovanni/harasan/xml_newdep/8/', '/works/csisv12/giovanni/harasan/xml_newdep/9/', '/works/csisv12/giovanni/harasan/xml_newdep/11/']

def __populateXML():
    xmlfiles = {}
    for d in dirs:
        for fl in listdir(d):
            xmlfiles[path.basename(fl).replace('.xml', '')] = path.join(d, fl)
    return xmlfiles

def __getScoreMapping():
    score = {}
    for ln in open(scorefile).readlines():
        cells = ln.strip().split(' ')
        qid = int(cells[0][13:])
        if any(qid == query for query in queries):
            pid = cells[2][:cells[2].index('_')]
            if pid not in score or score[pid] > int(cells[3]):
                score[pid] = int(cells[3])
    return score

def __copyFileToDest(fl):
    copyfile(fl, path.join(destDir, path.basename(fl)))

def __getRelatedXML(dictxmlpath, score):
    displayholder = set()
    for ln in open(tsvfile).readlines():
        cells = ln.split('\t')
        qid = int(cells[0][13:])
        if any(qid == query for query in queries):
            paper = cells[2][:cells[2].index('_')]
            if paper in score and score[paper] > 0 and paper in dictxmlpath:
                __copyFileToDest(dictxmlpath[paper])
            elif paper in score and score[paper] > 0 and paper not in displayholder:
                print paper
                displayholder.add(paper)

if __name__ == '__main__':
    xmlad = __populateXML()
    score = __getScoreMapping()
    __getRelatedXML(xmlad, score)

