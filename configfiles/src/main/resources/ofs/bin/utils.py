# $Source: /usr/local/cvs/scripts/deploy/bin/utils.py,v $
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
# Version $Id: utils.py,v 1.36 2009/04/20 08:03:31 kmanickam Exp $
#
"""
Small general-purpose python utilities
Some are replacements for Python 2.2+ features not found in our jython2.1
"""

import os, sys, os.path, re, shutil, md5
import log

# ---------------------- general utils ----------------------

xcls = ""
def findFiles(classpath, dirname, files):
    global xcls
    for n in files:
        classpath = classpath+":"+os.path.join(dirname,n)
    xcls = xcls+":"+classpath

def findFileListAndJoin(dirPath):
    global xcls
    visit = findFiles
    classpath = ""
    os.path.walk(dirPath, visit, classpath)
    return xcls

def childOfDir(p, destDir):
    """final path of p if copied to destDir"""
    if not os.path.isdir(destDir): 
        raise Exception, "%s is not a dir" % destDir
    return pjoin(destDir, os.path.basename(p))

def copyStuff(src, destdir, verbose=1):
    """copy files or dirs under a dest dir"""
    if not os.path.exists(src): 
        return
    dest = destdir
    if os.path.exists(destdir): 
        dest = childOfDir(src, destdir)
    if verbose:
        log.summary("  copying", src)
    if os.path.isdir(src): 
        shutil.copytree(src, dest)
    else:
        shutil.copy2(src, dest)

def die(*strings):
    log.fatal(strings)
    sys.exit(1)

def replaceSingleQuoteByDouble(value):
    return re.sub(r"'", r"''", value)

def replaceSingleSlashByDouble(path):
    return re.sub(r"\\", r"\\\\", path)

def replaceDoubleSlashBySingle(path):
    return re.sub(r"\\\\", r"\\", path)

def dospath(path):
    return re.sub(r"/", r"\\", path)

def dropSuffix(path):
    """Returns string less suffix(string)"""
    suffixes = path.split(".")
    return ".".join(suffixes[:-1])

def endsWith(str, suffix, regExp=0):
    if(regExp == 0):
        return str[-len(suffix):] == suffix
    else :
        regex = re.compile(suffix)
        return regex.match(str)     

def fileAppend(src, dest):
    """appends contents of src to end of dest"""
    writeFile(dest, readFile(src), "a")

def flatten(*args):
    list = []
    for arg in args: 
        if type(arg) in (type(()),type([])):
            for elem in arg:
                list.extend(flatten(elem))
        else: 
            list.append(arg)
    return list

def dirListFilt(dir):
    """Filtered, sorted listdir"""
    raw = os.listdir(dir)
    excludes = "CVS tmp".split()
    cleaned = [ x for x in raw if excludes.count(x) == 0]
    return sorted(cleaned)

def makePath(path):
    """Makes a directory path, unless it doesn't need to :-)"""
    if not os.path.exists(path):
        os.makedirs(path)

def move(src, dest):
    """rename (even if dest exists on Windows)
    shutil.move not avail in Jython 2.1"""
    if os.path.isfile(dest): os.unlink(dest)
    os.rename(src, dest)

def oatedgeRunning(config):
    """Use oatedge.{bat,sh} status to determine if OAT Edge is running"""
    
    if osname() == "nt":
        command = pjoin(config["APP_HOME"], "..", "oatedge.bat")
    else:
        command = pjoin(config["APP_HOME"], "conf", "oatedge")

    cmd = syspath(command) + " status"

    (err, text) = _runSysCommand(cmd)
    if err != 0:
        log.summary(cmd)
        log.summary(text)
        raise Exception, "OAT Edge status check failed\nUse -f to bypass status check"
    else:
        return re.search("Service Manager: Running", text)

def osname():
    """Workaround jython misconceptions of os.name"""
    if os.name == 'java':
        try: 
            import javashell
            name = javashell._getOsType()  # jython patch 27Oct04
        except: #ImportError, AttributeError
            name = os._osType  # jython 2.1
        return name
    else:
        return os.name

def parseProperties(lines):
    """Input can be an sort of .properties, .bat, or .sh file that follows the
    convention 'key = value'"""

    regex = re.compile(r"\s*(\w+)\s*=(.*)")

    config = {}
    for line in lines:
        m = regex.match(line)
        if m:
            config[m.group(1)] = m.group(2).strip()
    return config

def parseDotedProperties(lines):
    """Input can be an sort of .properties, .bat, or .sh file that follows the
    convention 'key.key1 = value'"""

    regex = re.compile(r"(.*)=(.*)")

    dotProps = {}
    for line in lines:
        m = regex.match(line)
        if m:
            dotProps[m.group(1)] = m.group(2).strip()
    return dotProps

def pjoin(*elements):
    """path join; takes variable args, not list; always uses '/' 

    Prefered over os.path.join for readability of paths.
    """
    return "/".join(elements)

def readlines(filename):
    """A substitute for open() iterator, which
    doesn't work in Jython 2.1"""
    f = open(filename)
    lines = f.readlines()
    f.close()
    return lines

def readFile(filename, mode="r"):
    """dunno if jython closes or not"""
    f = open(filename,mode)
    text = f.read()
    f.close()
    return text

def rmStuff(path, verbose=1):
    """Removes files and dir-trees,
    but doesn't complain if they don't exist"""
    if not os.path.exists(path):
        return
    if verbose:
        log.summary("  removing", path)
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)

def sorted(list):
    """Returns a sorted copy of list
    unlike list.sort(), which is inplace"""
    a = list[:]
    a.sort()
    return a

def suffix(path):
    """Returns character after last period
    but does not include the dot.
    Returns '' if no suffix"""
    suffixes = path.split(".")
    if len(suffixes) == 1:
        return ""
    else:
        return suffixes[-1]

def syspath(path):
    """return path formated appropriate for current OS"""
    if osname() == "nt":
        return dospath(path)
    else:
        return unixpath(path)

def sysCommand(command, effectiveDir=None, returnStdout=None, noPrintCmd=None):
    """Runs os.system on cleaned up cmd, capturing output.

    If set, chdirs to effectiveDir first"""

    # Note workaround: os.chdir not supported in Jython, but && works both
    # Windows & Unix
    try:
        if effectiveDir:
            command = "cd %s && %s" % (effectiveDir, command)

        cmd = syspath(command)

        if noPrintCmd == None:
            log.detail(cmd)
        (err, text) = _runSysCommand(cmd)
        text = text.rstrip()
        if text:
            log.detail(text)
        if err != 0:
            if noPrintCmd == None:
                log.error("System command failed:", cmd)
        if returnStdout:
            return text
        else:
            return err
    except Exception, why:
        log.exception()
        die("Failed to execute sys command\n",str(why))

def unixpath(path):
    return re.sub(r"\\", r"/", path)

def writeFile(filename, text, mode="w"):
    """replace open().write() for jython, which doesn't close on exit"""
    f = open(filename, mode)
    f.write(text)
    f.close()
    

def signature(filename): 
    """Return the MD5 signature for a given file (name) ignoring whilespaces"""
    data = readFile(filename).replace('\n','').replace('\r','').replace(' ','').replace('\t','')
    hexstring = md5.md5(data).hexdigest()
    return hexstring

def isValidSigFile(filename, absFileName):
    """Checks to see if the given file should be signed"""
    if (not os.path.isfile(absFileName)):
        return 0
    if (filename == ".signatures"):
        return 0
    if filename.startswith("#"):
        return 0
    if filename.endswith("~"):
        return 0
    if filename.endswith(".pid"):
        return 0
    if filename.startswith("license") and filename.endswith(".txt"):
        return 0
    if filename in ["oatstarted", "oatstarted_NOT", "oatstarted_NOT_TOMCAT", "des-config.xml"]:
        return 0
    if absFileName.find("/.kettle/") >= 0:
        return 0
    if (filename == "eenms.properties"):
        return 0
    return 1

def createSignatureFile(dirpath):
    """Creates a .signatures file at the given directory"""
    log.detail("Creating signature file for " + dirpath.replace('\\', '/'))
    filenames = dirListFilt(dirpath)
    sigFileName = pjoin(dirpath, ".signatures")
    sigFile = open(sigFileName, "w")
    for filename in filenames:
        absFileName = pjoin(dirpath, filename)
        if isValidSigFile(filename, absFileName):
            sig = signature(absFileName)
            sigFile.write("%s\t%s\n" % (filename, sig))
    sigFile.close()

def visitToCreate(arg, dirpath, filenames):
    """Wrapper function used by os.path.walk"""
    basename = os.path.basename(dirpath)
    createSignatureFile(dirpath)

def createSignatureFileRec(dirpath):
    """Create signature files recursively starting at the given directory"""
    os.path.walk(dirpath, visitToCreate, None)

def loadSignatureFile(dirpath):
    """Returns a dictionary of file names and signatures from
    the signature file at the given directory"""
    result = {}

    sigFileName = pjoin(dirpath, ".signatures")
    sigFile = open(sigFileName, "r")
    lines = sigFile.readlines()
    
    for line in lines:
        (filename, sig) = line.split("\t")
        result[filename.strip()] = sig.strip()
    sigFile.close()
    return result

def checkSignatureFile(dirpath):
    """Checks the contents of the given directory against its .signatures
    file. Returns whether differences are found"""
    log.detail("Checking contents of " + dirpath.replace('\\', '/') + " against stored signatures")

    hasDiff = 0

    try: 
        sigMap = loadSignatureFile(dirpath)
    except IOError, e:
        log.summary("ERROR: Could not open the .signatures at %s: %s" % (dirpath, e))
        return 1
    
    filenames = dirListFilt(dirpath)
    for filename in filenames:
        absFileName = pjoin(dirpath, filename)
        if isValidSigFile(filename, absFileName):
            sig = signature(absFileName)
            try:
                oldSig = sigMap[filename]
                if (oldSig != sig):
                    log.summary("ERROR: Modified File: %s" % (absFileName))
                    hasDiff = 1
                del sigMap[filename]
            except KeyError:
                log.summary("ERROR: Added File: %s" % (absFileName))
                hasDiff = 1

    for missingFileName in sigMap.keys():
        log.summary("ERROR: Removed File: %s/%s" % (dirpath, missingFileName))
        hasDiff = 1

    return hasDiff

def visitToCheck(hasDiffList, dirpath, filenames):
    """Wrapper function for os.path.list. Builds a list of booleans
    that determine whether/not there are differences"""
    basename = os.path.basename(dirpath)
    curDiff = checkSignatureFile(dirpath)
    hasDiffList.append(curDiff)
    return hasDiffList

def checkSignatureFileRec(dirpath):
    """Recursively checks for differences between the .signatures file
    and the contents of the directory. Returns whether/not there are differences"""
    hasDiffList = []
    os.path.walk(dirpath, visitToCheck, hasDiffList)
    return reduce(lambda oldDiff, curDiff: oldDiff or curDiff, hasDiffList, 0)

confSubDirs = "customscenarios dmspec metadata scenarios webapp wsdl".split()

def createConfSignatureFiles(confDir):
    """Creates .signatures files under the given conf directory"""
    createSignatureFile(confDir)
    subDirs = confSubDirs
    for subDir in subDirs:
        createSignatureFileRec(pjoin(confDir, subDir))

def checkConfSignatureFiles(confDir):
    """Checks .signatures files under the given conf directory. Returns whether/not
    differences were found"""
    hasDiff = checkSignatureFile(confDir)
    subDirs = confSubDirs
    for subDir in subDirs:
        # Don't short-circuit
        curDiff = checkSignatureFileRec(pjoin(confDir, subDir))
        hasDiff = hasDiff or curDiff
    return hasDiff        


# ---------------------- helpers ----------------------

try:
    import popen2
    def _runSysCommand(cmd):    
        # Note: Popen4 is not in standard Jython2.1
        # As popen-maintainer suggests, I've patched our jython
        # with javaos, javashell, and popen2.py (as of 27Oct04)
        # This also add WinServer2003 to osTypes :-) 
        child = popen2.Popen4(cmd)
        text  = child.fromchild.read() 
        err   = child.wait()
        return (err, text)

except:
    # print "USING BACKUP OS.SYSTEM"
    def _runSysCommand(cmd):
        return (os.system(cmd), "")

