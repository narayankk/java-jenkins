# $Source: /usr/local/cvs/scripts/deploy/bin/mergeXml.py,v $
#
# Copyright (c) 1999-2004 OAT Systems, Inc.  All Rights Reserved.
#
# This software is the confidential and proprietary information
# (Confidential Information) of OAT Systems, Inc.  You shall not
# disclose or use Confidential Information without the express written
# agreement of OAT Systems, Inc.
#
#
# Author     : Vadim Pesochinskiy
# Version $Id: mergeXml.py,v 1.6.22.1 2005/04/06 17:00:13 sfinley Exp $
#

import sys, os, getopt
import xml.sax, xml.sax.handler
import java
import com
import log, utils

def mergeXml(src, dest):
    xmlMerge(dest, src, dest)

def xmlMerge(origfile, changefile, outfile, verbose=0):
    if not os.path.exists(origfile):
        createStubXml(changefile, origfile)

    try:
        _xmlMerge(origfile, changefile, outfile)
    except (IOError, os.error), why:
        log.error("Can't merge %s to %s: %s" % (`changefile`, `origfile`, str(why)))
    except:
        if verbose: raise
        else: log.exception("xmlMerge failed %s to %s" % (`changefile`, `origfile`))

def _xmlMerge(origfile, changefile, outfile):
    xmerge = com.oatsystems.devtool.xmerge.XMerge()
    xmerge.parsePrimary(origfile)
    xmerge.merge(changefile)
    xmerge.write(outfile)


class FindTopNode(xml.sax.saxutils.DefaultHandler):
    def __init__(self):
        self.top = ""

    def startElement(self, name, attrs):
        if self.top:
            return
        self.top = name

# Several custom xml config files ship missing from project.  Since _xmlMerge
# will fail if origfile missing or empty, this means folks can use .xml.m files
# in plugins.  OTOH, replacing .xml wholesale (even for custom_*.xml) is
# unfriendly to each other.  So this createStubXml will create a one node XML
# file that can be merged to.  This works great in many cases:
#   custom_eventmap.xml
#   custom_reportmap.xml
#   custom_urlmap.xml
# This might not work for the multilevel config files:
#   custom_tabs.xml
#   custom_navlinks.xml
# because merge xml can only merge if parent nodes already exist.  For these
# files, folks can just merge to non-custom versions.

def createStubXml(sample, output):

    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)
    dh = FindTopNode()
    parser.setContentHandler(dh)

    try:
        parser.parse(sample)
        utils.writeFile(output, "<%s/>\n" % dh.top)
    except:
        log.exception("createStubXml failed", sample)
        
def main():
    # This syntax was intendended to mimic copy but I question it now.

    usage = "usage: %s [-v] [-i infile] changefile destfile" \
            % os.path.basename(sys.argv[0])
    try:
        (opts, args) = getopt.getopt(sys.argv[1:], 'vi:')
    except getopt.GetoptError:
        sys.exit(usage)
    if len(args) != 2: 
        sys.exit(usage)
    (changefile, destfile) = args
    infile = destfile
    verbose = 0
    for o, val in opts:
        if o == "-i":
            infile = val
        if o == "-v":
            verbose = 1

    xmlMerge(infile, changefile, destfile, verbose)

if __name__ == "__main__":
    main()

