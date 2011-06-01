#!/usr/bin/env python
from random import random, choice
from lxml import etree
from optparse import OptionParser


class cache:
    def __init__(self, f):
        self._f = f
        self._d = {}

    def __call__(self, x):
        if x in self._d:
            return self._d[x]
        else:
            y = self._f(x)
            self._d[x] = y
            return y


# contain the namespace of dmoz xml file (kinda hacky)
def ns():
    return "{http://dmoz.org/rdf/}"


def r():
    return "{http://www.w3.org/TR/RDF/}"


# return the list of links of category cat.
def links(cont_root, cat):
    for t in cont_root.iter(ns()+"Topic"):
        if cat == t.attrib[r()+"id"]:
            return [n.attrib[r()+"resource"] for n in t.iter() if "link" in n.tag]
    return None


# given a category (like Top/Arts/Architecture) collect a maximum of n
# links over the categories cats.
def collectLinks(cont_root, cats, n):
    l = []
    for cat in cats:
        l += links(cont_root, cat)
        if len(l) >= n:
            return l[:n]
    return l


# collects up to n links in BFS order from category cat
def collectLinksBFS(const_root, struct_root, cat, n):
    cats = [cat]
    l = []
    s = len(l)
    while s < n and len(cats) > 0:
        l += collectLinks(const_root, cats, n - s)
        s = len(l)
        if s < n:
            cats = sum([subcategories(struct_root, cat) for cat in cats],[])
        else:
            return l[:n]
    return l

# return the list of direct subcategories of cat. If there isn't such
# cat then it returns the empty list.
def subcategories(struct_root, cat):
    for t in struct_root.iter(ns()+"Topic"):
        if cat == t.attrib[r()+"id"]:
            return [n.attrib[r()+"resource"] for n in t.iter() if "narrow" in n.tag]
    return []


# given a category choose randomly a subcategory from it. p is the
# probability to choose a subcategory which is not a direct child of
# cat. struct_root is the root element of the structure.rdf.u8 file.
def chooseSubcategory(struct_root, cat, p):
    l = subcategories(struct_root, cat)
    if l:
        sc = choice(l)
        if random() <= p:
            scr = chooseSubcategory(struct_root, sc, p)
            if scr:
                sc = scr
        return sc
    else:
        return None


# return a list of pairs of categories
def chooseSubcategoriesPairs(structureFileName, options):
    structureFile = open(structureFileName)

    print "Parse", structureFileName
    st = etree.parse(structureFile)

    pf = lambda:chooseSubcategory(st.getroot(), options.posCR, options.rp)
    nf = lambda:chooseSubcategory(st.getroot(), options.negCR, options.rp)

    print "Choose subcategories"
    res = set()
    while len(res) < options.s:
        res.add((pf(),nf()))
    return res


def build_techtc(contentFileName, structureFileName, options):
    sp=chooseSubcategoriesPairs(structureFileName, options)
    print "sp =", sp
    
    # contentFile = open(contentFileName)
    # print "Parse", contentFileName
    # cTree = etree.parse(contentFile)


def main():
    usage = "Usage: %prog CONTENT_RDF_FILE STRUCTURE_RDF_FILE"
    parser = OptionParser(usage)
    parser.add_option("-p", "--positive-category-root",
                      dest="posCR", default="Top/Arts",
                      help="Category root of the sub-categories used for positive documents. [default: %default]")
    parser.add_option("-n", "--negative-category-root",
                      dest="negCR", default="Top/Science",
                      help="Category root of the sub-categories used for negative documents. [default: %default]")
    parser.add_option("-r", "--recursive-probability", type="float",
                      dest="rp", default=0.5,
                      help="Probability of searching in the ODP in depth. [default: %default]")
    parser.add_option("-s", "--techtc-size", type="int",
                      dest="s", default=300,
                      help="Size of the techtc generated. [default: %default]")
    (options, args) = parser.parse_args()

    if len(args) != 2:
        parser.error("incorrect number of arguments. Use --help to get more information")

    contentFileName=args[0]
    structureFileName=args[1]

    build_techtc(contentFileName, structureFileName, options)

if __name__ == "__main__":
    main()
