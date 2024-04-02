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
# Author     : Vadim Pesochinskiy
# Version $Id$
#

import sys, os
import logging
import utils
import traceback

logger = None

def init(logDir, type=None):
    global logger
    
    if logger:
        summary("Changing logger output to", logDir)
    if not os.path.isdir(logDir):
        fatal("log.init: Not a directory", logDir)
        sys.exit(1)

    debugfileName = "/deploy_detail.log"
    if (type == "startup"):
        debugfileName = "/launch_messages.log"

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    addStreamHandler(sys.stdout,
                     logging.INFO,
                     "%(message)s")

    if (type == None):
        addFileHandler(logDir + "/deploy_summary.log",
                   logging.INFO,
                   "%(asctime)s %(message)s",
                    "%Y-%m-%d %H:%M")

    addFileHandler(logDir + debugfileName,
                   logging.DEBUG,
                   "%(asctime)s %(message)s")

def addStreamHandler(stream, level, format):
    _addHandler(logging.StreamHandler(stream), level, format)

def addFileHandler(filename, level, format, dateFmt=None):
    _addHandler(logging.FileHandler(filename), level, format, dateFmt)

def _addHandler(hdlr, level, format, dateFmt=None):
    hdlr.setFormatter(logging.Formatter(format, dateFmt))
    hdlr.setLevel(level)
    logger.addHandler(hdlr) 


def fatal(*strings):
    _log(logging.CRITICAL, "FATAL ERROR:", strings)

def exceptionString():
    """Returns the current exception type and description."""
    # unlike str(why), this includes exception type
    exctype, value = sys.exc_info()[:2]
    return ("".join(traceback.format_exception_only(exctype, value))).strip()

def exception(*strings):
    _log(logging.ERROR, exceptionString(), strings)

def error(*strings):
    _log(logging.ERROR, "ERROR:", strings)

def warn(*strings):
    _log(logging.WARNING, "WARNING:", strings)

def summary(*strings):
    _log(logging.INFO, strings)

def detail(*strings):
    _log(logging.DEBUG, strings)

def _log(level, *strings):
    text = " ".join(map(str, utils.flatten(strings)))
    try:
        logger.log(level, text)
    except AttributeError:
        print >>sys.stderr, text

def _test():
    s = "This is a"
    t = "pre-init message"

    fatal(s, "FATAL", t)
    error(s, "ERROR", t)
    warn(s, "WARN", t)
    summary(s, "SUMMARY", t)
    detail(s, "DETAIL", t)

    init("..")

    t = "post-init message"

    fatal(s, "FATAL", t)
    error(s, "ERROR", t)
    warn(s, "WARN", t)
    summary(s, "SUMMARY", t)
    detail(s, "DETAIL", t)

    exception(s, "NO-EXCEPTION", t)
    try: 
        1/0
    except: 
        exception()
        exception(s, "AN-EXCEPTION", t)

if __name__ == "__main__":
    _test( )

