#!/usr/bin/env python
import os
import sys
import pickle
from random import seed, random, choice
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
            y = self._f(*x)
            if len(self._d) < self._s:
                self._d[x] = y
            self._failures += 1
            return y
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


def collectLinksBFS(cat, options):
    '''collects up to n links in BFS order from category cat.'''
    cats = [cat]
    l = []
    s = len(l)
    n = options.l
    while s < n and len(cats) > 0:
        l += collectLinks(options.c, cats, n - s)
        s = len(l)
        if s < n:
            cats = sum([csubcategories((options.s, cat, tuple(options.subtopic_tags)))
                        for cat in cats],[])
        else:
            return l[:n]
    return l


def choiceCollectLinks(cat, options, m = -1):
    '''randomly choose a set of links belonging to a category (or its
    subcategories). If after m attempts the number of links n hasn't
    been reached (considering that duplicated links are ignored) then
    it returns the empty set. If m is negative then there is no limit
    in the number of attempts (which can lead to infinit loop). p is
    the probability to dig deeper in the hierarchy to get the links.'''
    res = set()
    n = options.l
    while len(res) < n and m != 0:
        scat = choiceCategory(cat, options)
        if scat:
            link = choiceLinks(options.c, scat)
            if link:
                if link not in res:
                    res.add(link)
                    print len(res), link
        m -= 1
    return res


def subcategories(structureFileName, cat, subtopic_tags):
    '''return the list of direct subcategories of cat. If there isn't
    such cat then it returns the empty list.'''
    sf = open(structureFileName)
    for _,t in etree.iterparse(sf, tag = ns()+"Topic"):
        if cat == t.attrib[r()+"id"]:
            l = [n.attrib[r()+"resource"] for n in t.iter()
                 if any((st in n.tag) for st in subtopic_tags)]
            t.clear()
            return l
        t.clear()
    sf.close()
    return []

csubcategories = Cache(subcategories, cache_size)

def choiceSubcategory(cat, options):
    '''given a category choose randomly a subcategory from it. p is
    the probability to choose a subcategory which is not a direct
    child of cat. struct_root is the root element of the
    structure.rdf.u8 file.'''
    
    l = csubcategories((options.s, cat, tuple(options.subtopic_tags)))
    p = options.rp
    if l:
        sc = choice(l)
        if random() <= p:
            scr = choiceSubcategory(sc, options)
            if scr:
                sc = scr
        return sc
    else:
        return None


def choiceCategory(cat, options):
    '''like choiceSubcategory but consider cat as a result too'''
    p = options.rp
    if random() <= p:
        return choiceSubcategory(cat, options)
    else:
        return cat


def choiceSubcategoriesPairs(options, spl):
    '''Given an initial set of pairs, insert a set of pairs of topics
    randomly chosen'''
    
    pf = lambda:choiceSubcategory(options.posCR, options)
    nf = lambda:choiceSubcategory(options.negCR, options)

    while len(spl) < options.S:
        p = (pf(), nf())
        if p not in spl:
            spl.add(p)
            print len(spl),p


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
    cmd += " -Rgif,jpeg,jpg,png,swf,css,rss,ico,js,wmv,mpeg,mpg,mp3,mov"
    cmd += " -Q" + str(options.Q)
    cmd += " \"" + link + "\""
    cmd += " -O \"" + doc_path_html(options, topic_id, doc_index) + "\""
    # TODO add program options for these parameters
    cmd += " -t 1"              # try only once
    cmd += " --random-wait"
    cmd += " --timeout=3"       # wait 3 sec max
    # cmd += " -q"
    return cmd


def html2text_cmd(topic_id, doc_index, options):
    cmd = "html2text"
    cmd += " -ascii"
    cmd += " -style pretty"
    cmd += " -o \"" + doc_path_txt(options, topic_id, doc_index) + "\""
    cmd += " " + doc_path_html(options, topic_id, doc_index)
    cmd += " &"                 # run in parallel to speed things up
    return cmd


def filterTopics(d, dcl, spl, minl):
    '''For each topic in d, dcl and spl, remove it if it doesn't have
    minl links in dcl'''

    nspl = {(p,n) for p,n in spl if len(dcl[p]) >= minl and len(dcl[n]) >= minl}
    if nspl:
        cats = set.union(*[set(pa) for pa in nspl])
    else:
        cats = set()
    ndcl = {x:dcl[x] for x in cats}
    nd = {x:d[x] for x in cats}
    return nd, ndcl, nspl


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
    tdc = techtc_doc_path(options, topic_id)
    print "Fill document",tdc,"in techtc format"
    rtdc = " >> " + "\"" + tdc + "\""
    cmd = "echo \"<dmoz_doc>\"" + rtdc
    # print cmd
    os.system(cmd)
    cmd = "echo id=" + str(doc_index) + rtdc
    # print cmd
    os.system(cmd)
    cmd = "echo \"<dmoz_subdoc>\"" + rtdc
    # print cmd
    os.system(cmd)
    cmd = "more " + doc_path_txt(options, topic_id, doc_index) + rtdc
    # print cmd
    os.system(cmd)
    cmd = "echo \"</dmoz_subdoc>\"" + rtdc
    # print cmd
    os.system(cmd)
    cmd = "echo \"</dmoz_doc>\"" + rtdc
    # print cmd
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

def dictCatLinks(spl, options, dcl):
    '''Insert dcl[topic]=links for each topic of spl not already in
    dcl. spl is a set of pairs of categories gotten from
    choiceSubcategoriesPairs'''

    if options.d:               # deterministic link selection
        f = lambda x: collectLinksBFS(x, options)
    else:                       # random link selection
        # TODO add options instead of that ad hoc number
        f = lambda x: choiceCollectLinks(x, options, options.l*100) 

    for psc,nsc in spl:
        if psc not in dcl:
            print "Select",options.l,"links for positive subcategory",psc
            dcl[psc] = f(psc)
        if nsc not in dcl:
            print "Select",options.l,"links for negative subcategory",nsc
            dcl[nsc] = f(nsc)


def dictTopicId(contentFileName, cats, d):
    '''Insert d[cat]=id for each category of cats not already in d'''
    cf = open(contentFileName)
    for _,t in etree.iterparse(cf, tag = ns()+"Topic"):
        topic = t.attrib[r()+"id"]
        if topic in cats and topic not in d:
            d[topic] = t.findtext(ns()+"catid")
            print "id("+topic+") =", d[topic]
        t.clear()
        if len(d) == len(cats):
            break
    cf.close()


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

def buildTopicsLinks(options):
    '''Build a triplet (d, dcl, spl) where d is a dictionary
    associating topics and ids, dcl is a dictionary associating topics
    and list of links, and spl is a set of pairs of topics (positive
    vs negative). Depending on the options a dump file can be provided
    in input so the building process will no start from scratch
    (usefull in case of crashing). For the same reason (if the right
    option is selected it can save preriodically the building in to a
    dump file).'''

    if options.i:               # start from a dump file
        print "The building will start from file", options.i
        inputDumpFile = open(options.i)
        d, dcl, spl = pickle.load(inputDumpFile)
    else:                       # start from scratch
        print "No dump file has been provided so the building will start from scratch"
        d = {}
        dcl = {}
        spl = set()

    while len(spl) < options.S:
        s = options.S - len(spl)
        print "Choose", s, "pairs of subcategories of", options.posCR, "and", options.negCR, "respectively"
        choiceSubcategoriesPairs(options, spl)
    
        print "Associate the id of each subcategory"
        cats = set.union(*[set(p) for p in spl])
        dictTopicId(options.s, cats, d)
    
        print "For each subcategory select", options.l, "links"
        dictCatLinks(spl, options, dcl)
        print "Total number of positive and negative subcategories =", len(dcl)

        minl = int(options.L * options.l)
        print "Remove pairs of topics with less than",minl,"links"
        l = len(spl)
        d, dcl, spl = filterTopics(d, dcl, spl, minl)
        print l - len(spl),"pairs have been removed"
    
    return d, dcl, spl
        
def build_techtc(options):

    seed(options.random_seed)
    
    d, dcl, spl = buildTopicsLinks(options)
    
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
    parser.add_option("-r", "--random-seed",
                      default=1,
                      help="Random seed. [default: %default]")
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
    parser.add_option("-R", "--recursive-probability", type="float",
                      dest="rp", default=0.5,
                      help="Probability of searching in the ODP in depth. [default: %default]")
    parser.add_option("-S", "--techtc-size", type="int",
                      dest="S", default=300,
                      help="Size of the techtc generated. [default: %default]")
    parser.add_option("-l", "--documents-number", type="int",
                      dest="l", default=200,
                      help="Number of documents per dataset. [default: %default]")
    parser.add_option("-L", "--minimum-proportion-document-number", type="float",
                      dest="L", default=0.9,
                      help="In case enough links cannot be retrieved to reach the right document number (option -l) then what proportion of it we tolerate. [default: %default]")
    parser.add_option("-d", "--deterministic-link-selection",
                      action="store_true", dest="d",
                      help="Select the links within a subcategory in BFS order (faster). Otherwise it is selected ramdonly (much slower).")
    parser.add_option("-o", "--output-directory",
                      dest="o", default="__default__",
                      help="Directory where to download the web pages and place the dataset collection. [default: techtc_SIZE] where SIZE is the size of the dataset collection given by option S. If option -P is used then it denotes the place where to dump the data collected during parsing. [default: techtc_SIZE.dump]")
    parser.add_option("-i", "--input-dump-file",
                      dest="i", default="",
                      help="Dump file to load so that the process of building the topics and links doesn't start from scratch. If no file is given then it starts from scratch. [default: %default].")
    parser.add_option("-Q", "--quota", type="int",
                      dest="Q", default=100000,
                      help="Maximum number of bytes to retreive per link. [default: %default]")
    parser.add_option("-P", "--only-parse", action="store_true",
                      dest="P",
                      help="Perform only parsing (building of topics and links), do not download web pages, and save the result in the file provided with options -o.")
    parser.add_option("-t", "--subtopic-tags", action="append",
                      default=["narrow"],
                      help="Use the following tag prefixes to find subtopics of a given topic.")
    (options, args) = parser.parse_args()

    if len(args) != 0:
        parser.error("incorrect number of arguments. Use --help to get more information")

    if options.o == "__default__":
        options.o = "techtc_"+str(options.S)
        if options.P:
            options.o = options.o+".dump"

    # if options.i == "__default__":
    #     options.i = "techtc_"+str(options.S)
    #     options.i = options.o+".dump"

    build_techtc(options)

    # print "Cache failures for links =", clinks.get_failures()
    # print "Cache hits for links =", clinks.get_hits()

    # print "Cache failures for subcategories =", csubcategories.get_failures()
    # print "Cache hits for subcategories =", csubcategories.get_hits()

if __name__ == "__main__":
    main()
