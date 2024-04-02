# $Source$
#
# Copyright (c) 1999-2004 OAT Systems, Inc.  All Rights Reserved.
#
# This software is the confidential and proprietary information
# (Confidential Information) of OAT Systems, Inc.  You shall not
# disclose or use Confidential Information without the express written
# agreement of OAT Systems, Inc.
#
#
# Author     : Chris Winters
# Version $Id$
#
from __future__ import nested_scopes

import os, sys, re
import log, utils

def replaceWASConfigVars(varsDict, text):
    """Using values from varsDict (typically from configVars)
    substitute variables of the form @KEY@.
    Input file is src, output is dest.""" 

    return replaceFlowerBraces(varsDict,replaceFlowerBraces(varsDict,replaceBraces(varsDict,text)))

def replaceBraces(varsDict, text):
    """Replace variables of the form @KEY@"""
    #see Python Cookbook p. 88
    joinedVars = "|".join(map(re.escape, varsDict.keys()))
    regex = re.compile("\$\((%s)\)" % joinedVars)
    return regex.sub(lambda match: varsDict[match.group(1)], text)

def replaceFlowerBraces(varsDict, text):
    """Replace variables of the form @KEY@"""
    #see Python Cookbook p. 88
    joinedVars = "|".join(map(re.escape, varsDict.keys()))
    regex = re.compile("\${(%s)}" % joinedVars)
    return regex.sub(lambda match: varsDict[match.group(1)], text)

def replaceConfigVars(varsDict, src, dest):
    """Using values from varsDict (typically from configVars)
    substitute variables of the form @KEY@.
    Input file is src, output is dest.""" 

    if len(varsDict.keys()) == 0: log.warn("configuration is empty")

    mode = "r"
    if utils.endsWith(src, ".bat.in"):
       mode = "rb"
    text = utils.readFile(src,mode)
    text = replaceAtAt(varsDict, text)
    utils.writeFile(dest, text, "wb") # binary yields unix newlines

def replaceAtAt(varsDict, text):
    """Replace variables of the form @KEY@"""
    #see Python Cookbook p. 88
    joinedVars = "|".join(map(re.escape, varsDict.keys()))
    regex = re.compile("@(%s)@" % joinedVars)
    return regex.sub(lambda match: varsDict[match.group(1)], text)

def sysExpandedCommand(configVars, command, effectiveDir=None, returnStdout=None, printCmd=None):
    """Run OS commands with @@ replacement, in effectiveDir."""
    return utils.sysCommand(replaceAtAt(configVars, command), effectiveDir, returnStdout, printCmd)

def main():
    import getopt
    import configVars

    usage = "usage: %s [-c config] infile outfile" \
            % os.path.basename(sys.argv[0])
    try:
        (opts, args) = getopt.getopt(sys.argv[1:], 'c:')
    except getopt.GetoptError:
        sys.exit(usage)
    if len(args) != 2: 
        sys.exit(usage)

    configfile = None
    for o, val in opts:
        if o == "-c":
            configfile = val

    config = configVars.load(configfile)
    replaceConfigVars(config, args[0], args[1])

if __name__ == "__main__":
    main()

