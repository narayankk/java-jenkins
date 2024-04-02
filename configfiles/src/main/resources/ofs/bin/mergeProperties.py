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
"""Given lines of the form 'key=value' in src and dest files,
replaces dest values with src values.

The ordering of src and dest are both preserved as much as possible.  Overridden
dest variables are comented out, other dest lines are left as is, and all src
lines are appended at bottom (better when src has comments)

Supports regular expression replacements when the property value is of
the form s/old-regexp/new-regexp. Multiple regular expressions can be
joined by semi-colons.

Also supports token based management where a property value of the
form @token:foo,bar ensures that foo and bar are either already
present or added in the property as tokens separated by commas. 
"""
import os, sys, re, shutil, getopt
import log, utils

def mergeProperties(src, dest):
    propertiesMerge(dest, src, dest)

def propertiesMerge(origfile, changefile, outfile):
    # create empty file if original is missing
    if not os.path.exists(origfile):
        utils.writeFile(origfile, "")
    
    try:
        _propertiesMerge(origfile, changefile, outfile)
    except (IOError, os.error), why:
        log.error("Can't merge %s to %s: %s" % (`changefile`, `origfile`, str(why)))

def isIncompleteLine(s):
     # Does the line end with an odd number of backslashes
     s = s.rstrip()
     if not s.endswith("\\"): 
         return 0
     if s.endswith("\\\\"):
         return isIncompleteLine(s[0:len(s)-2])
     return 1
 
def _propertiesMerge(origfile, changefile, outfile):
    changeLines = utils.readlines(changefile)
    changeHash = hashLines(changeLines)
    origLines = utils.readlines(origfile)
    outBackup = outfile+"~"
    if os.path.exists(outfile):
        shutil.copy2(outfile, outBackup)
    else:
        outBackup = ""

    try:
        out = open(outfile, "wb")

        regex = re.compile(r"\s*(%s)\s*=" % "|".join(changeHash.keys()))

        oldProps = {}
        # This holds all lines that end with \ before the current line
        linePrefix = ""
        for nextLine in origLines:
            if isIncompleteLine(nextLine):
                # The line ends with an odd number of backslashes
                # Remove CR/CR-LF from line prefix
                nextLine = nextLine.rstrip()

                # Append it to previous line prefix
                linePrefix = linePrefix + nextLine[0:len(nextLine)-1].lstrip()
                continue
            else:
                # Set the line for this iteration, including CR/CR-LF
                line = linePrefix + nextLine
                
                # This is for the next iteration
                linePrefix = ""
                

            m = regex.match(line)
            if m:
                # A line of the form key=value 
                out.write("# replaced by %s below\n" % changefile)
                out.write("# %s" % line)

                # Add the value to a dictionary (oldProps) in case it is modified using s/.../... syntax
                eqPos = int(line.find("="))
                key = line[0:eqPos].strip()
                value = line[eqPos + 1:].strip()
                oldProps[key] = value
            else:
                # Not a line of the form key=value 
                out.write(line)

        out.write("\n#### added by %s\n" % changefile)
        for line in changeLines:
            m = regex.match(line)
            if not(m):
                # Just print the line
                out.write(line)
            else:
                # A line of the form key=value 
                eqPos = int(line.find("="))
                key = line[0:eqPos].strip()
                value = line[eqPos + 1:].strip()

                if value.find("s/") == 0:
                    # This value is of the form s/.../...;s/.../...;...
                    try:
                        modValue = oldProps[key]
                        for searchReplExp in value[2:].split(";s/"):
                            out.write("# Applying %s to %s\n" % (searchReplExp, modValue))
                            firstSlash = searchReplExp.find("/")
                            searchExp = searchReplExp[0:firstSlash]
                            replExp = searchReplExp[firstSlash+1:]
                            modValue = re.sub(searchExp, replExp, modValue)
                        out.write("%s=%s\n" % (key, modValue))
                    except KeyError:
                        out.write("# WARN: Key %s is missing in the original file. Could not apply regular expression %s\n" % (key, value));
                elif value.find("@tokens:") == 0:
                    # This value is of the form @tokens:...,...,...
                    tokens = stripList(value[8:].split(","))

                    # Find original text
                    try:
                        modValue = oldProps[key]

                        # Separate the tokens with comma
                        prevTokens = stripList(modValue.split(","))
                        out.write("# Adding tokens %s to value %s in key %s\n" % (tokens, modValue, key))
                    except KeyError:
                        # There is no existing property
                        #out.write("# Adding tokens %s to originally missing property %s\n" % (tokens, key))
                        prevTokens = []

                    # Find out duplicate tokens
                    dupTokens = filter(lambda x, d=prevTokens: x in d, tokens)
                        
                    # Remove duplicate tokens from tokens
                    tokens = filter(lambda x, d=dupTokens: x not in d, tokens)

                    # Add the different ones to prevTokens
                    prevTokens.extend(tokens)

                    # Join back the tokens with ','
                    modValue = ",".join(prevTokens)
                    out.write("%s=%s\n" % (key, modValue))
                else:
                    # Just print the line
                    out.write(line)

        out.close()
        if outBackup:
            os.remove(outBackup)
    except:
        out.close()
        # Not sure if this will always work on Windows; 
        # Sometimes Win seems to think file not really closed
        if outBackup:
            utils.move(outBackup, outfile)
        raise # reraise

def hashLines(lines):
    hashTbl = {}
    regex = re.compile(r"\s*(\S+)\s*[+\-]?=")
    for line in lines:
        if len(line) == 0: continue
        if line[0] == '#': continue
        j = line.find("=")
        if j > 1:
            m = regex.match(line[:j+1])
            if m:
                hashTbl[m.group(1)] = line
    return hashTbl

def stripList(lst):
    # Remove spaces before & after the string, and remove empty strings in the list
    return filter(lambda x: len(x) > 0, map(lambda x: x.strip(), lst))
               
def main():
    usage = "usage: %s [-i infile] changefile destfile" \
            % os.path.basename(sys.argv[0])
    try:
        (opts, args) = getopt.getopt(sys.argv[1:], 'i:')
    except getopt.GetoptError:
        sys.exit(usage)
    if len(args) != 2: 
        sys.exit(usage)
    (changefile, destfile) = args
    infile = destfile
    for o, val in opts:
        if o == "-i":
            infile = val
    propertiesMerge(infile, changefile, destfile)

if __name__ == "__main__":
    main()
