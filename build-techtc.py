#!/usr/bin/env python
import os
import sys
import pickle
from random import random, choice
from lxml import etree
from optparse import OptionParser

# maximum cache size
cache_size = sys.maxint

class Cache:
    '''Simple cache without replacement. f is the function to cache. s
    is the size of the cache'''
    def __init__(self, f, s):
        self._f = f
        self._d = {}
        self._s = s
        self._calls = 0
        self._failures = 0

    def __call__(self, x):
        self._calls += 1
        if x not in self._d:
            if len(self._d) < self._s:
                self._d[x] = self._f(*x)
            else:
                return self._f(*x)
            self._failures += 1
        return self._d[x]

    def get_failures(self):
        return self._failures

    def get_calls(self):
        return self._calls

    def get_hits(self):
        return self._calls - self._failures


def ns():
    '''contain the namespace of dmoz xml file (kinda hacky)'''
    return "{http://dmoz.org/rdf/}"


def r():
    return "{http://www.w3.org/TR/RDF/}"


def links(contentFileName, cat):
    '''return the list of links of category cat.'''
    cf = open(contentFileName)
    for _,t in etree.iterparse(cf, tag = ns()+"Topic"):
        if cat == t.attrib[r()+"id"]:
            l = [n.attrib[r()+"resource"] for n in t.iter() if "link" in n.tag]
            t.clear()
            return l
        t.clear()
    cf.close()
    return None

clinks = Cache(links, cache_size)

def choiceLinks(contentFileName, cat):
    '''Choose randomly a link belonging to cat. If no link exists it
    returns None'''
    l = clinks((contentFileName, cat))
    if l:
        return choice(l)
    else:
        return None


def collectLinks(contentFileName, cats, n = None):
    '''given a set of categories collect a maximum of n links over the
    categories cats.'''
    l = []
    for cat in cats:
        l += clinks((contentFileName, cat))
        if n and len(l) >= n:
            return l[:n]
    return l


def collectLinksBFS(contentFileName, structureFileName, cat, n):
    '''collects up to n links in BFS order from category cat.'''
    cats = [cat]
    l = []
    s = len(l)
    while s < n and len(cats) > 0:
        l += collectLinks(contentFileName, cats, n - s)
        s = len(l)
        if s < n:
            cats = sum([subcategories(structureFileName, cat) for cat in cats],[])
        else:
            return l[:n]
    return l


def choiceCollectLinks(contentFileName, structureFileName, cat, n, p, m = -1):
    '''randomly choose a set of links belonging to a category (or its
    subcategories). If after m attempts the number of links n hasn't
    been reached (considering that duplicated links are ignored) then
    it return None. If m is negative then there is no limit in the
    number of attempts (which can lead to infinit loop). p is the
    probability to dig deeper in the hierarchy to get the links.'''
    res = set()
    while len(res) < n and m != 0:
        scat = choiceCategory(structureFileName, cat, p)
        if scat:
            link = choiceLinks(contentFileName, scat)
            if link:
                if link not in res:
                    res.add(link)
        m -= 1
    return res


def subcategories(structureFileName, cat):
    '''return the list of direct subcategories of cat. If there isn't
    such cat then it returns the empty list.'''
    sf = open(structureFileName)
    for _,t in etree.iterparse(sf, tag = ns()+"Topic"):
        if cat == t.attrib[r()+"id"]:
            l = [n.attrib[r()+"resource"] for n in t.iter() if "narrow" in n.tag]
            t.clear()
            return l
        t.clear()
    sf.close()
    return []

csubcategories = Cache(subcategories, cache_size)

def choiceSubcategory(structureFileName, cat, p):
    '''given a category choose randomly a subcategory from it. p is
    the probability to choose a subcategory which is not a direct
    child of cat. struct_root is the root element of the
    structure.rdf.u8 file.'''
    
    l = csubcategories((structureFileName, cat))
    if l:
        sc = choice(l)
        if random() <= p:
            scr = choiceSubcategory(structureFileName, sc, p)
            if scr:
                sc = scr
        return sc
    else:
        return None


def choiceCategory(structureFileName, cat, p):
    '''like choiceSubcategory but consider cat as a result too'''
    if random() <= p:
        return choiceSubcategory(structureFileName, cat, p)
    else:
        return cat


def choiceSubcategoriesPairs(options):
    '''return a set of pairs of categories randomly choosen'''
    
    pf = lambda:choiceSubcategory(options.s, options.posCR, options.rp)
    nf = lambda:choiceSubcategory(options.s, options.negCR, options.rp)

    res = set()
    while len(res) < options.S:
        res.add((pf(),nf()))
    return res


def topic_dir(options, topic_id):
    return options.o + "/" + topic_id

def topic_path(options, topic_id):
    return topic_dir(options, topic_id) + "/topic.txt"

def doc_path(options, topic_id, doc_index):
    return topic_dir(options, topic_id) + "/" + "doc_" + str(doc_index)

def doc_path_html(options, topic_id, doc_index):
    return doc_path(options, topic_id, doc_index) + ".html"

def doc_path_txt(options, topic_id, doc_index):
    return doc_path(options, topic_id, doc_index) + ".txt"

def techtc_doc_path(options, topic_id):
    return topic_dir(options, topic_id) + "/techtc_doc.txt"

def wget_cmd(topic_id, doc_index, link, options):
    cmd = "wget"
    cmd += " -r"
    cmd += " -np"
    cmd += " -linf"
    cmd += " -Rgif,jpeg,jpg,png,swf,css,rss,ico,js"
    cmd += " -Q" + str(options.Q)
    cmd += " " + link
    cmd += " -O \"" + doc_path_html(options, topic_id, doc_index) + "\""
    cmd += " -q"
    return cmd


def html2text_cmd(topic_id, doc_index, options):
    cmd = "html2text"
    cmd += " -ascii"
    cmd += " -style pretty"
    cmd += " -o \"" + doc_path_txt(options, topic_id, doc_index) + "\""
    cmd += " " + doc_path_html(options, topic_id, doc_index)
    return cmd


def createDocuments(dcl, d, options):
    '''Create documents in techtc format given dcl, a dictionary
    mapping all subcategories and a set of links (web pages), and bd,
    a dict associating topics and their ids'''

    # create directory to put the documents
    print "Create techtc directory"
    mkdir_cmd = "mkdir " + options.o
    print mkdir_cmd
    os.system(mkdir_cmd)

    for c in dcl:
        print "Download all links of",c
        print "Create topic directory"
        mkdir_cmd = "mkdir " + topic_dir(options, d[c])
        print mkdir_cmd
        os.system(mkdir_cmd)
        print "Added file containing the topic"
        topic_cmd = "echo " + c + " > " + topic_path(options, d[c])
        print topic_cmd
        os.system(topic_cmd)
        print "Start downloading links"
        downloadLinks(d[c], dcl[c], options)

def fillTechtcFormatDocument(options, topic_id, doc_index):
    print "Fill document in techtc format"
    tdc = techtc_doc_path(options, topic_id)
    rtdc = " >> " + "\"" + tdc + "\""
    cmd = "echo \"<dmoz_doc>\"" + rtdc
    print cmd
    os.system(cmd)
    cmd = "echo id=" + str(doc_index) + rtdc
    print cmd
    os.system(cmd)
    cmd = "echo \"<dmoz_subdoc>\"" + rtdc
    print cmd
    os.system(cmd)
    cmd = "more " + doc_path_txt(options, topic_id, doc_index) + rtdc
    print cmd
    os.system(cmd)
    cmd = "echo \"</dmoz_subdoc>\"" + rtdc
    print cmd
    os.system(cmd)
    cmd = "echo \"</dmoz_doc>\"" + rtdc
    print cmd
    os.system(cmd)
        
def downloadLinks(topic_id, ls, options):
    '''Download links ls and place the content of each link in a file
    under topic_id directory. The files are indexed from 0 to
    len(ls)-1'''

    i = 0
    for l in ls:
        # download links
        cmd = wget_cmd(topic_id, i, l, options)
        print cmd
        os.system(cmd)
        # convert them into text
        cmd = html2text_cmd(topic_id, i, options)
        print cmd
        os.system(cmd)
        # fill document in techtc format for that topic
        fillTechtcFormatDocument(options, topic_id, i)
        i += 1

def dictCatLinks(spl, options):
    '''Create a dictionary mapping each subcategory to a set of
    links. spl is a set of pairs of categories gotten from
    choiceSubcategoriesPairs'''

    res = {}
    
    if options.d:               # deterministic link selection
        f = lambda x: collectLinksBFS(options.c, options.s, x, options.l)
    else:                       # random link selection
        f = lambda x: choiceCollectLinks(options.c, options.s, x, options.l, options.rp, options.l*100)

    for psc,nsc in spl:
        print "Select",options.l,"links of positive subcategory",psc
        if psc not in res:
            res[psc] = f(psc)
        print "Select",options.l,"links of negative subcategory",nsc
        if nsc not in res:
            res[nsc] = f(nsc)
    return res


def dictTopicId(contentFileName, cats):
    '''Return a dict mapping categories to ids. cats is supposed to
    be a set so there is no redundant element'''
    d = {}
    cf = open(contentFileName)
    for _,t in etree.iterparse(cf, tag = ns()+"Topic"):
        topic = t.attrib[r()+"id"]
        if topic in cats:
            d[topic] = t.findtext(ns()+"catid")
            print topic, "has id", d[topic]
        t.clear()
    cf.close()
    return d


def dataset_dir(options, bd, p, n):
    return options.o + "/" + "Exp_" + bd[p] + "_" + bd[n]


def organizeDocuments(spl, bd, options):
    for p,n in spl:
        dsd = dataset_dir(options, bd, p, n)
        dsd_p = dsd + "/all_pos.txt"
        dsd_n = dsd + "/all_neg.txt"
        print "Create dataset directory for " + p + "vs" + n
        cmd = "mkdir " + dsd
        print cmd
        os.system(cmd)
        print "Move the positve documents in it"
        cmd = "mv " + techtc_doc_path(options, bd[p]) + " " + dsd_p
        print cmd
        os.system(cmd)
        print "Move the negative documents in it"
        cmd = "mv " + techtc_doc_path(options, bd[n]) + " " + dsd_n
        print cmd
        os.system(cmd)    

        
def build_techtc(options):
    if options.C:               # use dump file from a previous parse
        inputDumpFile = open(options.i)
        d, dcl, spl = pickle.load(inputDumpFile)
    else:
        print "Choose", options.S, "pairs of subcategories of", options.posCR, "and", options.negCR, "respectively"
        spl = choiceSubcategoriesPairs(options)
    
        print "Associate the id of each subcategory"
        cats = set.union(*[set(p) for p in spl])
        d = dictTopicId(options.s, cats)
    
        print "For each subcategory select", options.l, "links"
        dcl = dictCatLinks(spl, options)
        print "Total number of positive and negative subcategories =", len(dcl)

        if options.P:               # only parse
            # dump d, dcl and spl
            outputLinksFile = open(options.o, "w")
            pickle.dump((d, dcl, spl), outputLinksFile)
            return
        
    print "Create documents in techtc format for all subcategories"
    createDocuments(dcl, d, options)

    print "Organize documents according to the list of pairs of subcategories"
    organizeDocuments(spl, d, options)


def main():
    usage = "Usage: %prog [Options]"
    parser = OptionParser(usage)
    parser.add_option("-c", "--content-file",
                      dest="c", default="content.rdf.u8",
                      help="ODP RDF content file. [default: %default]")
    parser.add_option("-s", "--structure-file",
                      dest="s", default="structure.rdf.u8",
                      help="ODP RDF structure file. [default: %default]")
    parser.add_option("-p", "--positive-category-root",
                      dest="posCR", default="Top/Arts",
                      help="Category root of the sub-categories used for positive documents. [default: %default]")
    parser.add_option("-n", "--negative-category-root",
                      dest="negCR", default="Top/Science",
                      help="Category root of the sub-categories used for negative documents. [default: %default]")
    parser.add_option("-r", "--recursive-probability", type="float",
                      dest="rp", default=0.5,
                      help="Probability of searching in the ODP in depth. [default: %default]")
    parser.add_option("-S", "--techtc-size", type="int",
                      dest="S", default=300,
                      help="Size of the techtc generated. [default: %default]")
    parser.add_option("-l", "--documents-number", type="int",
                      dest="l", default=200,
                      help="Number of documents per dataset. [default: %default]")
    parser.add_option("-d", "--deterministic-link-selection",
                      action="store_true", dest="d",
                      help="Select the links within a subcategory in BFS order (faster). Otherwise it is selected ramdonly (much slower).")
    parser.add_option("-o", "--output-directory",
                      dest="o", default="__default__",
                      help="Directory where to download the web pages and place the dataset collection. [default: techtc_SIZE] where SIZE is the size of the dataset collection given by option S. If option -P is used then it denotes the place where to dump the data collected during parsing. [default: techtc_SIZE.dump]")
    parser.add_option("-i", "--input-dump-file",
                      dest="i", default="__default__",
                      help="Dump file to load in case options -C is used. [default: techtc_SIZE.dump] where SIZE is the size of the dataset collection given by option -S.")
    parser.add_option("-Q", "--quota", type="int",
                      dest="Q", default=100000,
                      help="Maximum number of bytes to retreive per link. [default: %default]")
    parser.add_option("-P", "--only-parse", action="store_true",
                      dest="P",
                      help="Perform only parsing and output on the Maximum number of bytes to retreive per link.")
    parser.add_option("-C", "--only-create-techtc", action="store_true",
                      dest="C",
                      help="Perform techtc creation given a techtc dump file gotten with option -P.")
    (options, args) = parser.parse_args()

    if len(args) != 0:
        parser.error("incorrect number of arguments. Use --help to get more information")

    if options.o == "__default__":
        options.o = "techtc_"+str(options.S)
        if options.P:
            options.o = options.o+".dump"

    if options.i == "__default__":
        options.i = "techtc_"+str(options.S)
        options.i = options.o+".dump"

    build_techtc(options)

    print "Cache failures for links =", clinks.get_failures()
    print "Cache hits for links =", clinks.get_hits()

    print "Cache failures for subcategories =", csubcategories.get_failures()
    print "Cache hits for subcategories =", csubcategories.get_hits()

if __name__ == "__main__":
    main()
