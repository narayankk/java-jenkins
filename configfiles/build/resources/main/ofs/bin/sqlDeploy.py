# $Source: /usr/local/cvs/scripts/deploy/bin/sqlDeploy.py,v $
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
# Author     : Krish Manickam
# Version $Id: sqlDeploy.py,v 1.30.44.1 2017/05/30 23:41:36 yzhu Exp $
#
"""Manage execution of a tree of sql files.

Expected directory structures is:
  module/version/db_type/*.sql
"""


import os, sys, time
import log, utils

from os.path import isdir, exists, basename
from utils import pjoin, suffix, dropSuffix

from replaceConfigVars import replaceConfigVars
from AbstractDeployer  import AbstractDeployer
import Jdbc

def sqlDeploy(configVars, path, packageDescription="", forceRedeployLast=0):
    if not isdir(path):
        return
    log.summary("  checking ", path)
    try:
        manager = SqlTreeManager(configVars, packageDescription, forceRedeployLast)
        if manager.deployTop(path) == 0:
             return 0
        manager.commit()
        manager.close()
        return 1
    except Exception:
        log.exception()
        return 0

# ---------------------- SqlTreeManager ----------------------



class SqlTreeManager:
    """Control execution of sql tree."""

    def __init__(self, config, packageName, forceRedeployLast=0):
        self.config = config
        self.packageName = packageName
        self.conn = Jdbc.openDbConn(config)
        self.forceRedeploy = forceRedeployLast

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def deployTop(self, path):
        if not isdir(path):
            return 1
        for m in utils.dirListFilt(path):
            modulePath = pjoin(path, m)
            if isdir(modulePath):
                if m == 'ALWAYS':
                    if self.deploySqlAlways(modulePath) == 0:
                        return 0
                elif m == 'zFINAL':
                    if self.deploySqlAlways(modulePath) == 0:
                        return 0
                else:
                    if self.deployModule(modulePath) == 0:
                        return 0
        return 1

    def deployModule(self, modulePath):
        if not isdir(modulePath):
            return 1
        try:
            currVer = int(self.getCurrModuleVersion(basename(modulePath)))
            log.detail("Version from DB", currVer)
        except Exception, why:
            log.exception()
            log.summary("Failed to get current schema version from version_info table\n",str(why))
            return 0
        for version in utils.dirListFilt(modulePath):
            try:
                vers = int(version)
            except ValueError:
                try:
                    if currVer < 100:
                        currVer = int(self.config["VERSION_PROP"])
                    ver = self.getVersion(version, currVer, modulePath)
                    vers = int(ver)
                except:
                    log.detail("Not excuting as this schema changes already available:", pjoin(modulePath,version))
                    if ver != "NA":
                        log.exception()
                    continue

            if vers > currVer or (vers == currVer and self.forceRedeploy):
                log.summary("  checking ", pjoin(modulePath,version))
                if self.deploySqlVersion(modulePath, version,vers) == 0:
                   return 0
                currVer = vers
        return 1

    def getVersion(self, version, curVer, modulePath):
        try:
            vers = version.split("-")
            modulePath=pjoin(modulePath,"../..")
            if self.isInUpgradePath(vers, curVer, modulePath) == 1:
               return vers[1]
            else:
               return "NA"
        except:
            log.summary("In getVersion method:")
            log.exception()
            return "NA"

    def isInUpgradePath(self, versions, curVer, modulePath):
        versionFile = modulePath + "/upgradePath.txt"
        if exists(versionFile):
            upgradePaths = utils.readlines(versionFile)
            log.detail("upgradepath",upgradePaths)
        else:
           log.error("file not exists:", pjoin(modulePath,"upgradePath.txt"))
           utils.die("File upgradePath.txt does not exist","")
        log.detail("Current Schema Version:",curVer)
        for upgradePath in upgradePaths:
           vers = upgradePath.split(",")
           foundCurVer = 0
           foundStartVer = 0
           try:
               for ver in vers:
                  iver = int(ver)
                  if int(iver) == int(curVer):
                     foundCurVer = 1
                  if int(iver) == int(versions[0]) and foundCurVer == 1:
                     foundStartVer = 1
                  if int(iver) == int(versions[1]) and foundStartVer == 1:
                     print "Yes, it is there..", versions[0], versions[1]
                     return 1
           except:
               log.exception()
               return 0
        return 0

    def fixBasenameBug(self, moduleName):
        """Fix bug in 3.0.2, 4.0.0, and 4.0.1 framework that used modulePath
        instead of basename(modulePath) for moduleName"""
        
        sql = """UPDATE version_info SET module_name = '%s' 
        where module_name like '%%/%s' """ % (moduleName, moduleName)

        self.conn.executeUpdate(sql)

    def getCurrModuleVersion(self, moduleName):
        self.fixBasenameBug(moduleName)

        sql = """select version_number from version_info
        where module_name = '%s' and is_latest = 'T'""" % moduleName
        result = self.conn.executeQuery(sql)
        if result == None:
            raise Exception, "Version query is broken"
        elif len(result) == 0:
            return -1
        elif len(result) == 1:
            if result[0]["version_number"] == None:
               return result[0]["VERSION_NUMBER"]
            else:
               return result[0]["version_number"]
        else:
            raise Exception, "version_info.is_latest is corrupt for %s" % moduleName

    def deploySqlAlways(self, modulePath):
        return self.runSqlDir(pjoin(modulePath, self.config["DB_TYPE"]))

    def deploySqlVersion(self, modulePath, version,ver):
        """Can be used from command line to force version reinstall"""
        if self.runSqlDir(pjoin(modulePath, version, self.config["DB_TYPE"])) == 0:
           return 0
        # record event, even if partial success
        self.recordModuleVersion(basename(modulePath), int(ver))
        return 1

    def runSqlDir(self, src):
        if not isdir(src):
            log.error(src, "is not a directory")
            return 

        log.summary("    executing", src)
        deployer = SqlDeployer(self.conn, self.config, src)
        deployer.customHook()
        return deployer.run()
        
    def recordModuleVersion(self, moduleName, vers):
        timestamp = "'%s'" % sqlTimeNow()
        if self.config["DB_TYPE"] == 'oracle':
            timestamp = "to_timestamp(%s, 'yyyy-mm-dd HH24:MI:SS')" % timestamp

        # Clear old before set new so to support forced redeploy of same version twice

        sql1 = """UPDATE version_info SET is_latest = 'F' 
        where module_name = '%s' """ % (
            moduleName)

        sql2 = """INSERT INTO version_info
        (module_name, version_number, patch_identifier, patch_ts, is_latest) 
        VALUES ('%s', '%s', '%s', %s, 'T')""" % (
            moduleName, vers, self.packageName, timestamp)

        self.conn.executeUpdate(sql1)
        self.conn.executeUpdate(sql2)



# ---------------------- SqlDeployer ----------------------

def sqlTimeNow():
    return time.strftime("%Y-%m-%d %H:%M:%S")

class SqlDeployer(AbstractDeployer):
    """Execute the .sql files in a directory

    Constructor typically given a versioned & db-typed subdir,
    e.g. sql/proj/0001/oracle

    Exported as 'deployer' to custom deploy scripts

    deployer.fileOrder is a list of sql-filenames to execute.  You can skip
    run() step by setting deployer.dorun = 0, or by invoking run() yourself.

    SQL is run using JDBC by default, but if deployer.sqlCmdLine is set, it
    will be used instead.  The config variables FILENAME, DIRNAME, and BASENAME
    will be set appropriately for this script, where FILENAME =
    DIRNAME/BASENAME.  For example,
      deployer.sqlCmdLine = "su - postgres psql oatdb -f @FILENAME@"   

    """

#    Alternatively, if deployer.useSqlCmdLine is true but deployer.sqlCmdline
#    is not set, the defaultSqlCmdLine will be used.  At present there are no
#    useful defaults.

    def __init__(self, conn, config, srcDir):
        AbstractDeployer.__init__(self, config, srcDir, "sql-deploy.py")
        self.setFileOrder(self.defaultFileOrder())
        self.conn = conn

        self.useSqlCmdLine = 0
        self.sqlCmdLine = ""

    def run(self):
        if not self.dorun: return
        self.dorun = 0

        for filename in self.fileOrder:
            f = pjoin(self.dir, filename)
            f_in = f+".in"
            if exists(f_in):
                replaceConfigVars(self.config, f_in, f)
            if self.runSqlFile(f) == 0:
                return 0
        return 1

    def runSqlFile(self, filename):
        log.summary("    sql:", filename)
        dbtype = self.config["DB_TYPE"]
        if self.useSqlCmdLine or self.sqlCmdLine:
            if not self.sqlCmdLine:
                self.sqlCmdLine = self.defaultSqlCmdLine()
            self.config["BASENAME"] = filename
            self.config["DIRNAME"]  = self.dir
            self.config["FILENAME"] = pjoin(self.dir, filename)
            self.syscmd(self.sqlCmdLine)
            return 1
        else:
            return Jdbc.runSqlFile(self.conn, filename, dbtype)

    def setFileOrder(self, fileString):
        """Sets order of sql file execution.
        
        Takes a string of whitespace-separated filenames
        >>> deployer.setFileOrder("first.sql second.sql")

        If using .sql.in files, specify name without .in
        """
        self.fileOrder = fileString.split()

    def defaultFileOrder(self):
        """Returns *.sql, after dropping .in suffixes."""
        forder = []
        for c in utils.dirListFilt(self.dir):
            if suffix(c) == "in":
                f = dropSuffix(c)
                if suffix(f) == "sql" and forder.count(f) == 0:
                    forder.append(f)
            elif suffix(c) == "sql":
                forder.append(c)                
        return " ".join(forder)

    def defaultSqlCmdLine(self):
        return "Do not know SQL cmd line"

def test():
    import sys, log
    import configVars

    for opt in sys.argv[1:]:
        if opt == "-q":
            log.init(os.environ.get("TEMP", "/tmp"))
    config = configVars.load()

    module = "test"
    try:
        manager = SqlTreeManager(config, "Test v2")
        sql = "delete from version_info where module_name = '%s'" % module
        manager.conn.executeUpdate(sql)

        for j in range(1,4):
            manager.recordModuleVersion("sample/bug/path/"+module, j)
        for j in range(4,7):
            v = manager.getCurrModuleVersion(module)
            print "version is", v
            manager.recordModuleVersion(module, j)
        manager.close()
    except Jdbc.DbError:
        log.exception()

if __name__ == "__main__":
    test()


