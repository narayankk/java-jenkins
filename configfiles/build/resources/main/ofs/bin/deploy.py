# $Source: /usr/local/cvs/scripts/deploy/bin/deploy.py,v $
#
# Copyright (c) 1999-2008 OAT Systems, Inc.  All Rights Reserved.
#
# This software is the confidential and proprietary information
# (Confidential Information) of OAT Systems, Inc.  You shall not
# disclose or use Confidential Information without the express written
# agreement of OAT Systems, Inc.
#
#
# Author     : Chris Winters
# Author     : Krish Manickam
# Version $Id: deploy.py,v 1.122 2016/01/11 21:21:49 wlam Exp $
#
"""
Preprocesses and copies install files to their proper locations.  

The build process provides extensions and config files in an archive that has
structure similar to intended conf, axis, and raf layout.

Each invocation of deployPlugins.py will reconstruct conf, axis, and raf from
scratch using product defaults and specified plugins.  Optionally, it can set
aside a backup of conf, axis, and raf first.

If package has both raf.war and raf directory, only the exploded form will be
used.  Similarly for axis.war and axis.
"""

import os, sys, re, shutil, glob, getopt, time, sys.stdin
import log, utils, configVars, version

from os.path import exists, isdir, isfile, basename, dirname
from utils import unixpath, pjoin, suffix, dropSuffix, endsWith

from replaceConfigVars import replaceConfigVars, sysExpandedCommand, replaceWASConfigVars
from mergeProperties   import mergeProperties
from mergeXml          import mergeXml
from sqlDeploy         import sqlDeploy
from AbstractDeployer  import AbstractDeployer

# Java imports 
from java.lang import *
from com.oatsystems.util.mdmgr import MetadataManager
from org.autoidcenter.util import EncryptionUtilities

# globals; some for sake of pyChecker
config = {}
appHome = ""
webappHome = ""
installHome = ""
doAction = {}
configFile = None
logDir = None
deployMetadata = 0
databaseCreation = 0
limitedDeploy = 0
forceDeploy = 0
deployAllMetadata = 0
forceRedeployLastSqlVersion = 0
ofsUpgrade = 0
onFederation = 0
noEARDeploy = 0
ofsUpgradeSchema = 0
changeStarPassword = 0
changeEaPassword = 0
changeLdapPassword = 0
changeSAPPassword = 0
changeWasPassword = 0
changeDbPassword = 0
changeDbHost = 0
changeEaDbHost = 0
changeStarDbHost = 0
reinstallWinService = 0
changeWSContext = 0
changeTomcatFolder = 0
changeJdkFolder = 0
newWSContext = ""
dbName = ""
eaDbName = ""
starDbName = ""
dbHostName = None
starDbHostName = None
eaDbHostName = None
edgeName = ""
edgeID = ""
dbPassword = ""
dbHost = ""
dbUser = ""
eaDbUser = ""
starDbUser = ""
starPassword = ""
eaPassword = ""
ldapPassword = ""
sapPassword = ""
wasPassword = ""
sapUser = ""
tnsName = None
ofsAppName = None
wasDMName = None
tomcatFolder = None
newConfigProps = None
jdkFolder = None
databaseLevel = "full"

# ./conf/files & subdirs that won't be kept in ./default/conf
confExcludes = """
    CMS.xml
    CMS.xml.in
    cmstemplates
    """.split()

# ---------------------- parseArgs ----------------------

actionList = "custom axis ui conf classes sql sql_ent sql_site sql_star bin lib oatentreports nano EdgeMQsetup ext oss schema mobile".split()

def parseArgs():
    global configFile, logDir, forceDeploy, forceRedeployLastSqlVersion, ofsUpgrade, onFederation, ofsAppName, noEARDeploy, ofsUpgradeSchema, deployAllMetadata, changeStarPassword, changeEaPassword, changeLdapPassword, changeSAPPassword, changeWasPassword, changeDbPassword, changeDbHost, dbHostName, dbName, edgeName, edgeID, dbUser, dbPassword, starPassword, eaPassword, ldapPassword, sapPassword, wasPassword, sapUser, deployMetadata, databaseCreation, databaseLevel, reinstallWinService, newWSContext, usage, wasDMName, changeTomcatFolder, changeJdkFolder, tomcatFolder, jdkFolder, newConfigProps

    usage = \
    """
usage: 
%s [-f | --force] [-s password | --starDbPassword=password] [-p password | --dbPassword=password] 
   [-e password | --eaDbPassword=password] [-a password | --ldapAdminPassword=password] 
   [{-A user -S password | --SAPuser=user --SAPpassword=password}] [-m | --deployMetadata]
   [-w password | --wasAdminPassword=password] [-u | --upgrade] [-r | --redeployLatestSqls] 
   [-D {full|partial} | --dbCreation={full|partial}] [-I xpressID | --xpressID=xpressID] 
   [-E xpressName | --xpressName=xpressName] [-n | --noEARDeploy] [-F ofsAppName | --federate=ofsAppName] 
   [-P dbUser | --dbUser=dbUser] [-d dbName | --dbName=dbName] [-H hostName | --dbHost=hostName]
   [-b dbUser | --eaDbUser=dbUser] [-B dbName | --eaDbName=dbName] [-j hostName | --eaDbHost=hostName]
   [-g dbUser | --starDbUser=dbUser] [-G dbName | --starDbName=dbName] [-J hostName | --starDbHost=hostName]
   [-K jdkFolder | --jdkFolder=jdkFolder] [-T tomcatFolder | tomcatFolder=tomcatFolder] [-q configProps]
   [-M dmgr | --deploymentManager=dmgr] [-C wsContxt | --wsContext=wsContext] [-o|x actions] [package...]
    If no packages specified, all of
        default, ext/*, local
    will be deployed.

    -a changes ldap admin password
    -A changes SAP AII user name
    -b Enterprise database user name
    -B Enterprise database name
    -C Webservice context name (default is axis)
    -d database name in which tables to be created
    -D create database tables; need to provide levels (full/partial)
    -e changes EA database password details in EDM
    -E OFS name like oatedge1 - unique name across the enterprise
    -f force; ignore signatures and status checks
    -F Application Name to Federate in WAS
    -g Star database user name
    -G Star database name
    -h print this help message
    -H Database host name
    -I OFS ID (4 digit hex value)
    -j Enterprise database hostname
    -J Star database hostname
    -K JDK Folder 
    -m deploy Metadata
    -M WAS Deployment Manager name
    -n Do not deploy EAR into WAS
    -o runs only specified actions
    -p sets database password details in OFS and used for DB creations
    -P database user name for DB creations
    -q config properties like \"a=b,c=d\"
    -r redeploys last version of each sql module (may cause sql errs)
    -s changes star database password details in OFS
    -S changes SAP AII user password
    -T tomcat folder
    -u OFS upgrade
    -w changes websphere admin password
    -W Windows service reinstall
    -x excludes specified actions
    actions is a comma-separated list with possible values:
        %s""" % (dropSuffix(os.path.basename(sys.argv[0])),
                 ",".join(actionList))
            
    try:
        (opts, args) = getopt.getopt(sys.argv[1:], 'a:A:b:B:c:C:D:d:e:E:fF:g:G:hH:iI:j:J:K:l:mM:no:O:p:P:q:rs:S:t:T:uUw:Wx:',["ldapAdminPassword=","help","dbCreation","deployMetadata","noEARDeploy","installMetadata","force", "federate=", "redeployLatestSqls", "reinstallWinService", "configFile=", "wsContext=","eaDbPassword=", "dbHost=", "logDir=", "runActions=", "dbPassword=", "starDbPassword=","SAPpassword=", "SAPuser=", "excludeActions=","upgrade","upgradeSchema","wasAdminPassword=","dbUser=","dbName=","xpressName=","xpressID=","deploymentManager=","starDbHost=","eaDbHost=","starDbUser=","eaDbUser=","eaDbName=","starDbName=","sslHost=","tnsName=","jdkFolder=","tomcatFolder=","configPropsChange="])
    except getopt.GetoptError, why:
        print why
        sys.exit(usage)

    setAllActions(1)
    for opt, val in opts:
        if opt in ('-h', '--help'):
            sys.exit(usage)
        elif opt in ('-c', '--configFile'):
            configFile = val
        elif opt in ('-C', '--wsContext'):
            newWSContext = val
            changeWSContext = 1
        elif opt in ('-l', '--logDir'):
            logDir = val
        elif opt in ('-o', '--runActions'):
            setAllActions(0)
            setActions(val, 1) 
        elif opt in ('-P', '--dbUser'):
            changeDbPassword = 1
            dbUser = val
        elif opt in ('-b', '--eaDbUser'):
            changeEaPassword = 1
            eaDbUser = val
        elif opt in ('-g', '--starDbUser'):
            changeStarPassword = 1
            starDbUser = val
        elif opt in ('-W', '--reinstallWinService'):
            reinstallWinService = 1
        elif opt in ('-I', '--xpressID'):
            changeDbPassword = 1
            edgeID = val
        elif opt in ('-E', '--xpressName'):
            changeDbPassword = 1
            edgeName = val
        elif opt in ('-t', '--tnsName'):
            tnsName = val
        elif opt in ('-d', '--dbName'):
            changeDbPassword = 1
            dbName = val
        elif opt in ('-B', '--eaDbName'):
            changeEaPassword = 1
            eaDbName = val
        elif opt in ('-G', '--starDbName'):
            changeStarPassword = 1
            starDbName = val
        elif opt in ('-d', '--dbHost'):
            changeDbHost = 1
            dbHostName = val
        elif opt in ('-j', '--eaDbHost'):
            changeEaDbHost = 1
            eaDbHostName = val
        elif opt in ('-J', '--starDbHost'):
            changeStarDbHost = 1
            starDbHostName = val
        elif opt in ('-p', '--dbPassword'):
            changeDbPassword = 1
            dbPassword = val
        elif opt in ('-s', '--starDbPassword'):
            changeStarPassword = 1
            starPassword = val
        elif opt in ('-e', '--eaDbPassword'):
            changeEaPassword = 1
            eaPassword = val
        elif opt in ('-w', '--wasAdminPassword'):
            changeWasPassword = 1
            wasPassword = val
        elif opt in ('-a', '--ldapAdminPassword'):
            changeLdapPassword = 1
            ldapPassword = val
        elif opt in ('-S', '--SAPpassword'):
            changeSAPPassword = 1
            sapPassword = val
        elif opt in ('-A', '--SAPuser'):
            sapUser = val
        elif opt in ('-x', '--excludeActions'):
            setActions(val, 0) 
        elif opt in ('-n', '--noEARDeploy'):
            noEARDeploy = 1
        elif opt in ('-F', '--federate'):
            onFederation = 1
            ofsAppName = val
        elif opt in ('-M', '--deploymentManager'):
            wasDMName = val 
        elif opt in ('-D', '--dbCreation'):
            databaseCreation = 1
            databaseLevel = val
            if databaseLevel == "full":
               deployAllMetadata = 1
               forceDeploy = 1
        elif opt in ('-f', '--force'):
            forceDeploy = 1
        elif opt in ('-m', '--deployMetadata'):
            deployMetadata = 1
        elif opt in ('-i', '--installMetadata'):
            deployAllMetadata = 1
        elif opt in ('-u', '--upgrade'):
            ofsUpgrade = 1
            forceDeploy = 1
        elif opt in ('-U', '--upgradeSchema'):
            ofsUpgradeSchema = 1
            forceDeploy = 1
        elif opt in ('-K', '--jdkFolder'):
            changeJdkFolder = 1
            jdkFolder = val
        elif opt in ('-T', '--tomcatFolder'):
            changeTomcatFolder = 1
            tomcatFolder = val
        elif opt in ('-q', '--configPropsChange'):
            newConfigProps = val
        elif opt in ('-r', '--redeployLatestSqls'):
            forceRedeployLastSqlVersion = 1

    ## Check to ensure that -i is set only with -f. This is to prevent accidental call to -i
    if deployAllMetadata and not forceDeploy:
        log.summary("The -i option should only be invoked from the installer. It should be accompanied by the -f option")
        sys.exit(usage)
    
    return args

def setAllActions(value):
    for k in actionList: doAction[k] = value

def setActions(commaString, value):
    for act in commaString.split(","):
        if doAction.has_key(act):
            doAction[act] = value
        else:
            print "No such action:", act

def reinstallWinServices():
    if utils.osname() == "nt":
       if config["START_UP"] == "yes":
          log.summary("Cleaning up old services")
          sysExpandedCommand(config, "sc.exe delete OATEdge_@SERVER_MODE@", appHome)
          sysExpandedCommand(config, "sc.exe delete OATTomcat_@SERVER_MODE@", appHome)
          sysExpandedCommand(config, "sc.exe delete OATEdgeMon_@SERVER_MODE@", appHome)
          sysExpandedCommand(config, "edge_monitor_svc.bat", appHome+"\\bin")
          sysExpandedCommand(config, "regedit.exe -s edge_monitor_svc.reg", appHome+"\\bin")
          if config["WS_TYPE"] == "Tomcat":
             log.summary("Reinstalling new services")
             sysExpandedCommand(config, "tomcatsvc.bat", appHome+"\\bin")
             sysExpandedCommand(config, "regedit.exe -s oat_tomcat.reg", appHome+"\\bin")
       else:
          log.summary("Service is not enabled, no action on Windows Service.")
           
def replaceConfigureProperties():
    configDir = configVars.scriptParent()
    mergeFile = configDir+"/dbpasswd.properties.m"
    origConfigFile = configDir+"/configure.properties.orig"
    configFile = configDir+"/configure.properties"

    if os.path.exists(origConfigFile):
         print "Taking  from backup of config property"
    else:
         print "Taking backup of config property"
         shutil.copy2(configFile,origConfigFile)

    if os.path.exists(mergeFile):
         os.remove(mergeFile);

    out = open(mergeFile, "wb")         

    out.write("DB_PASSWORD_ENCRYPTED=true\n")

    if (tnsName != None and tnsName != ""):
       out.write("DB_TNS_NAME="+tnsName+"\n")

    if changeJdkFolder == 1:
       if (jdkFolder == None or jdkFolder == ""):
           out.close();
           sys.exit(usage)
       out.write("JAVA_HOME="+utils.syspath(jdkFolder)+"\n")

    if (newConfigProps != None):
       for newConfigProp in newConfigProps.split(","):
           if newConfigProp.find("=") > 0:
               out.write(newConfigProp+"\n")
           else:
               out.close();
               sys.exit(usage)

    if changeTomcatFolder == 1:
       if (tomcatFolder == None or tomcatFolder == ""):
           out.close();
           sys.exit(usage)
       out.write("CATALINA_HOME="+utils.syspath(tomcatFolder)+"\n")
       out.write("CATALINA_BASE="+utils.syspath(tomcatFolder)+"\n")
       out.write("TOMCAT_INSTALL_DIR="+os.path.basename(tomcatFolder)+"\n")

    if changeWSContext == 1:
       out.write("WS_CONTEXT="+newWSContext+"\n")

    if changeDbPassword == 1:
       if (dbPassword == None or dbPassword == ""):
           out.close();
           sys.exit(usage)
       newPasswdEnc = EncryptionUtilities.encryptString(dbPassword)
       out.write("DB2_DB_PASSWORD="+newPasswdEnc+"\n")
       out.write("ORACLE_DB_PASSWORD="+newPasswdEnc+"\n")
       out.write("SQLSERVER_DB_PASSWORD="+newPasswdEnc+"\n")
       if (dbUser != None and dbUser != ""):
           out.write("DB2_DB_USER="+dbUser+"\n")
           out.write("ORACLE_DB_USER="+dbUser+"\n")
           out.write("SQLSERVER_DB_USER="+dbUser+"\n")
       if databaseCreation == 1:
           if (edgeName != None and edgeName != ""):
               out.write("OATEDGE_NAME="+edgeName+"\n")
           else:
               out.close();
               sys.exit(usage)
           if (edgeID != None and edgeID != ""):
               out.write("OATEDGE_SERIAL_NUMBER="+edgeID+"\n")
           else:
               out.close();
               sys.exit(usage)
           if (dbName != None and dbName != ""):
               out.write("DB_NAME="+dbName+"\n")
               out.write("DB_SERVICE="+dbName+"\n")
               out.write("ENTERPRISE_DB_SERVICE="+eaDbName+"\n")
           else:
               out.close();
               sys.exit(usage)
           if changeDbHost == 1:
               if (dbHostName != None and dbHostName != ""):
                   out.write("DB_HOST="+dbHostName+"\n")
               else:
                   out.close();
                   sys.exit(usage)
    if changeStarPassword == 1:
       if (starPassword == None or starPassword == ""):
           out.close();
           sys.exit(usage)
       starPasswd = EncryptionUtilities.encryptString(starPassword)
       out.write("STAR_DB_PASSWORD="+starPasswd+"\n")
       if (starDbUser != None and starDbUser != ""):
           out.write("STAR_DB_USER="+starDbUser+"\n")
       if databaseCreation == 1:
           if (dbStarHostName != None and dbStarHostName != ""):
               out.write("STAR_DB_HOST="+dbStarHostName+"\n")
           else:
               out.close();
               sys.exit(usage)
           if (starDbName != None and starDbName != ""):
               out.write("STAR_DB_NAME="+starDbName+"\n")
               out.write("STAR_DB_SERVICE="+starDbName+"\n")
           else:
               out.close();
               sys.exit(usage)
           if changeStarDbHost == 1:
               if (starDbHostName != None and starDbHostName != ""):
                   out.write("STAR_DB_HOST="+starDbHostName+"\n")
               else:
                   out.close();
                   sys.exit(usage)
    if changeEaPassword == 1:
       if (eaPassword == None or eaPassword == ""):
           out.close();
           sys.exit(usage)
       eaPasswd = EncryptionUtilities.encryptString(eaPassword)
       out.write("ENTERPRISE_DB_PASSWORD="+eaPasswd+"\n")
       if (eaDbUser != None and eaDbUser != ""):
           out.write("ENTERPRISE_DB_USER="+eaDbUser+"\n")
       if databaseCreation == 1:
           if (dbEaHostName != None and dbEaHostName != ""):
               out.write("ENTERPRISE_DB_HOST="+dbEaHostName+"\n")
           else:
               out.close();
               sys.exit(usage)
           if (eaDbName != None and eaDbName != ""):
               out.write("ENTERPRISE_DB_NAME="+eaDbName+"\n")
               out.write("ENTERPRISE_DB_SERVICE="+eaDbName+"\n")
           else:
               out.close();
               sys.exit(usage)
           if changeEaDbHost == 1:
               if (eaDbHostName != None and eaDbHostName != ""):
                   out.write("ENTERPRISE_DB_HOST="+eaDbHostName+"\n")
               else:
                   out.close();
                   sys.exit(usage)
    if changeLdapPassword == 1:
       if (ldapPassword == None or ldapPassword == ""):
           out.close();
           sys.exit(usage)
       ldapPasswd = EncryptionUtilities.encryptString(ldapPassword)
       out.write("USER_OAT_ADMIN_PASSWD="+ldapPasswd+"\n")
    if changeWasPassword == 1:
       if (wasPassword == None or wasPassword == ""):
           out.close();
           sys.exit(usage)
       wasPasswd = EncryptionUtilities.encryptString(wasPassword)
       out.write("WAS_ADMIN_USER_PASSWD="+wasPasswd+"\n")
    if changeSAPPassword == 1:
       if (sapPassword == None or sapPassword == "" or sapUser == None or sapUser == ""):
           out.close();
           sys.exit(usage)
       sapPasswd = EncryptionUtilities.encryptString(sapPassword)
       out.write("SAP_AII_USER="+sapUser+"\n")
       out.write("SAP_AII_PASSWORD="+sapPasswd+"\n")


    out.close()
    print "Merging the password changes"

    mergeProperties(mergeFile, configFile)

    if os.path.exists(mergeFile):
         os.remove(mergeFile);

# ---------------------- main ----------------------

def main():
    global config, appHome, webappHome, installHome, limitedDeploy, onFederation, wsContext, ofsAppName, wasDMName

    packages = parseArgs()

    if (newConfigProps != None or changeStarPassword == 1 or changeDbPassword == 1 or changeEaPassword == 1 or changeLdapPassword == 1 or changeSAPPassword == 1 or changeWSContext == 1 or changeDbHost == 1 or changeEaDbHost == 1 or changeStarDbHost == 1 or changeTomcatFolder == 1 or changeJdkFolder == 1):
        print "Changing basic configuration details"
        replaceConfigureProperties()

    config = configVars.deployInit(logDir, configFile)
    appHome    = config["APP_HOME"]
    webappHome = config["WEBAPP_HOME"]
    wsContext = config["WS_CONTEXT"]
    installHome = config["INSTALL_HOME"]
    if config["WEBAPP_PORT"] == "" or config["WEBAPP_PORT"] == None:
        config["WEBAPP_PORT"] = "9080"
    if config["OATEDGE_PORT"] == "" or config["OATEDGE_PORT"] == None:
        config["OATEDGE_PORT"] = "9080"
    if wasDMName == None:
         wasDMName = config["WAS_APPSERVER"]
         if wasDMName != None and wasDMName != "":
             print ("WAS Deployment Manager - "+wasDMName +"is extracted from configure.properties")

    config["WAS_APPSERVER"] = wasDMName

    if deployMetadata == 1:
        print "Deploying property metadata"
        deployOnlyMetadata()
        return 0

    if onFederation == 1:
        if ofsAppName == None or wasDMName == None or wasDMName == "":
            print ("OFS Application name and WAS deployment manager names have to be provided")
            sys.exit(usage)
        if config["SSL_ENABLE"] == "true":
            config["WEBAPP_PORT"] = "$OAT.https.port$"
            config["OATEDGE_PORT"] = "$OAT.https.port$"
        else:
            config["WEBAPP_PORT"] = "$OAT.http.port$"
            config["OATEDGE_PORT"] = "$OAT.http.port$"
        config["LIB_DIR"] = "$OAT.conf.dir$"
        config["APP_HOME"] = "$OAT.conf.dir$"
        config["CONF_DIR_URL"] = "$OAT.conf.dir$"
        if utils.osname() == "nt":
            config["CONF_DIR_URL"] = "/$OAT.conf.dir$"
        config["DSN"] = "$OAT.dsn$"
        config["OATEDGE_SERIAL_NUMBER"] = "$OAT.id$"
        config["OATEDGE_NAME"] = "$OAT.name$"
        config["OATEDGE_EPC"] = "FFFFFFFFFFFFFFF$OAT.name$F$OAT.name$"
        config["SOAP_SSL_PORT"] = "$OAT.soap.ssl.port$"
        config["SSL_PORT"] = "$OAT.https.port$"
        oatPort = config["OATEDGE_PORT"]
        webappPort = config["WEBAPP_PORT"]
        ccsServer = config["CCS_SERVER_HOST"]
        ccsServerPort = config["CCS_SERVER_PORT"]
        config["USER_ENT_SOAP_URL"] = "http://%s:%s/%s/services" % (ccsServer, ccsServerPort, wsContext)
        config["SOAP_URL"] = "http://localhost:%s/%s/services" % (webappPort, wsContext)
        config["OATEDGE_SOAP_URL"] = "http://localhost:%s/%s/services" % (webappPort, wsContext)
        config["SOAP_ADMIN_URL"] = "http://localhost:%s/%s/services/AxisServlet" % (webappPort, wsContext)
        config["OATEDGE_SOAP_ADMIN_URL"] = "http://localhost:%s/%s/services/AxisServlet" % (webappPort, wsContext)
    else:
        ofsAppName = "OFS_"+config["SERVER_MODE"]


    if config["WS_TYPE"] == "WebSphere":
        webappHome = appHome + "/websphere_tmp"
        if exists(webappHome):
            utils.rmStuff(webappHome)
        utils.makePath(pjoin(webappHome,"axis"))
        if config["SERVER_MODE"] == "EDM":
            utils.makePath(pjoin(webappHome,"oatentreports"))
        utils.makePath(pjoin(webappHome,uidir()))
    else:
        onFederation = 0
        

# Comment out this check until have a chance to test on Unix
#    if not forceDeploy and utils.oatedgeRunning(config):
#        log.error("Stop OAT Edge service first")

    finishedString = "Finished deploy"
    if ofsUpgrade == 1:
        finishedString = "Finished upgrade of file sets"
        log.summary("Starting Upgrade")
        if upgradeOFS() == 0:
           log.summary("Upgrade of fileset FAILED")
        replaceConfigureProperties()
        log.summary(finishedString)
        print ""
        log.summary("******* Run deploy -U ********")
        print ""
        return 0

    if ofsUpgradeSchema == 1:
        finishedString = "Finished upgrade"
        log.summary("Starting Schema Upgrade")
        if upgradeSchema() == 0:
           log.summary("Schema Upgrade FAILED")
           return 1
        reinstallWinServices()
        log.summary("Completed Schema upgrade and product upgrade")
 
    # Check to see if the signatures under the conf directory are valid
    if utils.checkConfSignatureFiles(appHome + "/conf"):
        # There are differences die
        if forceDeploy:
            log.summary("Deploy running with force option. Ignoring signature mismatches under %s/conf" % (appHome))
        else:
            utils.die("Signature mismatches under %s/conf. Re-run deploy with -f (force) option" % (appHome))

    if packages:
        log.summary("Starting limited deploy with local changes")
        limitedDeploy = 1
        for p in packages:
            deployPackage(utils.unixpath(os.path.abspath(p)))
        for p in listPlugins("local"):
            if deployPackage(unixpath(p)) == 0:
                log.summary("FATAL Error in deploying \"" + p +"\"")
                return
    else:
        if databaseCreation == 1:
           if databaseLevel == "full":
              log.summary("Starting Database Creation")
              deployStdDirAtSameLocation(appHome+"/schema")
              deployStdDirAtSameLocation(appHome+"/conf")
              deployStdDirAtSameLocation(appHome+"/bin")
              os.system("dbcreate.bat "+dbPassword)
              log.summary("Database creation done for "+dbName)
           else:
              log.summary("Starting Database updation from OARs")
        else:
           log.summary("Starting full deploy")
        deployAll()

    if databaseCreation == 1:
        deployOnlyMetadata()
        log.summary("Database changes are done for "+dbName)
        return 0

    if (changeStarPassword == 1 or changeDbPassword == 1):
        shutil.copy2(appHome + "/conf/webapp/app_properties.properties", appHome+"/default/"+wsContext+"/WEB-INF/classes/app_properties.properties")
        shutil.copy2(appHome + "/conf/webapp/app_properties.properties", webappHome+"/"+wsContext+"/WEB-INF/classes/app_properties.properties")
        if config["SERVER_MODE"] != "EDM":
            shutil.copy2(appHome + "/conf/webapp/app_properties.properties", appHome+"/default/oatedge/WEB-INF/classes/app_properties.properties")
            shutil.copy2(appHome + "/conf/webapp/app_properties.properties", webappHome+"/oatedge/WEB-INF/classes/app_properties.properties")

    # make sure oatedge webapp not starting on EDM
    if config["SERVER_MODE"] == "EDM":
        try:
            os.rename(webappHome+"/oatedge/WEB-INF/web.xml", webappHome+"/oatedge/WEB-INF/web.xml.not_start")
        except OSError:
            pass

    if config["WS_TYPE"] == "WebSphere":
        deployEAR()
    # Re-create signature files
    log.summary("Recreating .signatures files under %s/conf" % (appHome))
    utils.createConfSignatureFiles(appHome + "/conf")

    if deployAllMetadata:
        deployOnlyMetadata()
    
    if (reinstallWinService == 1):
        reinstallWinServices()

    log.summary(finishedString)
    return 0

def deployOnlyMetadata():
    mdHome = appHome + "/conf/metadata"
    if not exists(mdHome):
        log.summary ("Missing ofs/conf/metadata directory. Will not deploy property metadata from files")
    elif not isdir(mdHome):
        log.summary ("************Error ofs/conf/metadata is not a directory************")
    else:
        if deployAllMetadata:
            log.summary("Deploying property metadata in install mode. Will insert all specified metadata entries")
        else:
            log.summary("Deploying property metadata in normal mode. Will respect ignoreMetadata.* entries in savant.properties")
        try:
            (str1, str2) = MetadataManager.runMain(mdHome, deployAllMetadata)
            printDetails(str1)
            printSummary(str2)
            log.summary("Done deploying property metadata")
        except:
            if (deployMetadata != 1):
                print ""
                print "* Metadata is not re-deployed because of datamodel changes. To re-deploy metadata run the following command."
                print "deploy -m "
                print ""
            else:
                print "Error: Error in deploying metadata. Refer ofs/log/oatedge_errors.log"

def printDetails(str):
    printDetailsOrSummary(str, 0)

def printSummary(str):
    printDetailsOrSummary(str, 1)

def printDetailsOrSummary(str, isSummary):
    prevLine = "";
    for line in str.splitlines():
        if (line.startswith(" ") or line.startswith("\t")):
            prevLine = prevLine + "\n" + line
        else: 
            logDetailOrSummary(prevLine, isSummary)
            prevLine = line
    logDetailOrSummary(prevLine, isSummary)

def logDetailOrSummary(str, isSummary):
    if len(str) == 0:
        return
    
    if isSummary:
        log.summary(str)
    else:
        log.detail(str)
        
def wsadmin(getPass, installOrUpdate, extn, appName):
        wasLogMsg = sysExpandedCommand(config, "\"@WAS_BIN_DIR@/wsadmin.@SCRIPT_EXT@\" @WAS_ADMIN_USER_NAME@ "+getPass+" @WAS_CONNTYPE_STRING@ -f @INSTALL_DIR@/setup/redeploy.jacl "+installOrUpdate+" "+appName+" @WAS_APPSERVER@ @INSTALL_DIR2@\\\\ofs\\\\"+prodName()+extn+" @WAS_LOGIN_ENABLED@ @WAS_ADMIN_GROUPS@", config["INSTALL_DIR"], 1,1) 
        return wasLogMsg

def deployEAR():
        log.summary("Creating EAR")
        getPass = ""
        extn = ".ear"
        installOrUpdate = "delete"
        if limitedDeploy == 1:
           installOrUpdate = "update"
           extn = ".zip"
           makeEAR(".zip")
           log.summary("Updating partial EAR (this will take some time)")
        else:
           makeEAR(".ear")
           if noEARDeploy == 1:
             log.summary("Created EAR. Need to deploy the EAR manually from WAS admin console.")
             return
           else:
             log.summary("Deploying EAR (this will take some time)")

        if config["WAS_ADMIN_USER_PASSWD"] != "" and config["WAS_ADMIN_USER_PASSWD"] != None:
           getPass = EncryptionUtilities.decryptString(config["WAS_ADMIN_USER_PASSWD"])

        wasLogMsg = wsadmin(getPass,installOrUpdate, extn, ofsAppName)

        if limitedDeploy != 1:
           outWAS = open("WAS.props", "wb")
           outWAS.write(wasLogMsg)
           outWAS.close()
           wasLogProps = utils.parseProperties(utils.readlines("WAS.props"))
           for k in utils.sorted(wasLogProps.keys()):
              log.detail(k, "=", wasLogProps[k])
           if wasLogProps.has_key("OFS_APP_INSTALL_LOCATION"):
              wasLogProps["APP_INSTALL_ROOT"] = replaceWASConfigVars(wasLogProps, wasLogProps["APP_INSTALL_ROOT"])
              wasLogProps["OFS_APP_INSTALL_LOCATION"] = replaceWASConfigVars(wasLogProps, wasLogProps["OFS_APP_INSTALL_LOCATION"])
              log.summary("Stoping the application Server")
              sysExpandedCommand(config, "\"@WAS_BIN_DIR@/stopServer.@SCRIPT_EXT@\" @WAS_ADMIN_USER_NAME@ "+getPass+" @WAS_APPSERVER@", config["INSTALL_DIR"], 1,1) 
              time.sleep(30)
              log.summary("Remove EAR folder "+wasLogProps["OFS_APP_INSTALL_LOCATION"])
              retryRemove = 1
              try:
                 utils.rmStuff(utils.syspath(wasLogProps["OFS_APP_INSTALL_LOCATION"]))
                 retryRemove = 0
              except:
                 pass
              if retryRemove == 1:
                 time.sleep(30)
                 try:
                    utils.rmStuff(utils.syspath(wasLogProps["OFS_APP_INSTALL_LOCATION"]))
                 except:
                    pass

              log.summary("Starting the application Server")
              sysExpandedCommand(config, "\"@WAS_BIN_DIR@/startServer.@SCRIPT_EXT@\" @WAS_ADMIN_USER_NAME@ "+getPass+" @WAS_APPSERVER@", config["INSTALL_DIR"], 1,1) 
           log.summary("Installing the application")
           wasLogMsg = wsadmin(getPass,"install", extn, ofsAppName) 
           if wasLogMsg.find("Error in deploying the OAT Application") > 0 or wasLogMsg.find("ConnectorNotAvailableException") > 0 or wasLogMsg.find("SocketTimeoutException") > 0:
              utils.die("Failed to deploy the application "  + prodName()+extn+" WebSphere Application Server may be down or timeout has occured. Exiting from EAR deploy.")

        if ofsUpgradeSchema == 1 and os.path.exists(config["INSTALL_DIR"]+"/ofs/upgrade/removeJars.zip"):
           log.summary("Removing jars which are not removed by WAS during upgrade")
           wasLogMsg = sysExpandedCommand(config, "\"@WAS_BIN_DIR@/wsadmin.@SCRIPT_EXT@\" @WAS_ADMIN_USER_NAME@ "+getPass+" @WAS_CONNTYPE_STRING@ -f @INSTALL_DIR@/setup/redeploy.jacl update "+ofsAppName+" @WAS_APPSERVER@ @INSTALL_DIR2@\\\\ofs\\\\upgrade\\\\remove.zip @WAS_LOGIN_ENABLED@ @WAS_ADMIN_GROUPS@", config["INSTALL_DIR"], 1,1) 

def makeEAR(extn):
    makeWAR("axis")
    makeWAR(uidir())
    modules=" axis.war " + uidir()+".war"
    if limitedDeploy == 0:
       modules=modules+" META-INF "

    if config["SERVER_MODE"] == "EDM":
       makeWAR("oatentreports")
       modules=modules+" oatentreports.war"
    
    if limitedDeploy == 0:
       deployStdDir(pjoin(config["CONF_DIR"],"META-INF"), utils.childOfDir("META-INF", webappHome))
    sysExpandedCommand(config, "/opt/java/openjdk/bin/jar -cf ../"+prodName()+extn+modules, webappHome)

    
def makeWAR(module):
    if (onFederation == 1):
        if (module == "axis"):
            shutil.copy2(appHome + "/conf/webapp/app_properties.properties", appHome+"/conf/app_properties.properties")
            shutil.copy2(appHome + "/conf/webapp/app_properties.properties.in", appHome+"/conf/app_properties.properties.in")
            utils.copyStuff(appHome+"/conf", pjoin(webappHome,module))
            if os.path.exists(utils.pjoin(utils.pjoin(webappHome,module),"conf","activemq-data")):
                utils.rmStuff(utils.pjoin(utils.pjoin(webappHome,module),"conf","activemq-data"))
            if os.path.exists(utils.pjoin(utils.pjoin(webappHome,module),"conf","thinedge")):
                utils.rmStuff(utils.pjoin(utils.pjoin(webappHome,module),"conf","thinedge"))
            if os.path.exists(utils.pjoin(utils.pjoin(webappHome,module),"conf",config["server_mode"])):
                utils.rmStuff(utils.pjoin(utils.pjoin(webappHome,module),"conf",config["server_mode"]))

            utils.copyStuff(appHome+"/activemq-data", utils.pjoin(utils.pjoin(webappHome,module),"conf"))
            utils.copyStuff(appHome+"/lib/thinedge", utils.pjoin(utils.pjoin(webappHome,module),"conf"))
            utils.copyStuff(appHome+"/lib/"+config["server_mode"], utils.pjoin(utils.pjoin(webappHome,module),"conf"))
        if os.path.exists(pjoin(webappHome,module)+"/WEB-INF/classes/app_properties.properties"):
             os.remove(utils.pjoin(webappHome,module)+"/WEB-INF/classes/app_properties.properties")

    if limitedDeploy == 0:
        if (sysExpandedCommand(config, "/opt/java/openjdk/bin/jar -cf ../"+module+".war *"  , pjoin(webappHome,module)) != 0):
            log.summary("Creation of " + module+".war is failed. Re-trying again with some delay...")
            time.sleep(10)
            if (sysExpandedCommand(config, "/opt/java/openjdk/bin/jar -cf ../"+module+".war *"  , pjoin(webappHome,module)) != 0):
                utils.die("Failed to create "  + module+".war in the second retry. Exiting from EAR deploy")
    else:
       utils.move(utils.pjoin(webappHome,module), utils.pjoin(webappHome,module)+".war")

def upgradeOFS():
    backupDefault()

    for p in listPlugins("default"):
      if deployPackage(unixpath(p)) == 0:
          log.summary("FATAL Error in deploying \"" + p +"\"")
          log.summary("Rolling back all the file changes")
          restoreDefault()
          deployAll()
          return 0

    return 1

def upgradeSchema():

    for g in "upgrade/*.oar".split():
      for p in listPlugins(g):
        if deployPackage(unixpath(p)) == 0:
            log.summary("FATAL Error in deploying \"" + p +"\"")
            log.summary("Rolling back all the file changes")
            restoreDefault()
            deployAll()
            return 0

    return 1

def restoreDefault():
    appDefault = appHome+"/default"
    appDefaultOld = appHome+"/default."+config["VERSION_PROP"]
    log.summary("Restoring", appDefault)
    try:
       utils.rmStuff(appDefault)
    except:
       pass

    utils.move(appDefaultOld, appDefault)


def backupDefault():
    getVersionFromProp()
    appDefault = appHome+"/default"
    appDefaultOld = appHome+"/default."+config["VERSION_PROP"]
    log.summary("Backing up", appDefault)
    try:
       utils.rmStuff(appDefaultOld)
    except:
       pass

    log.summary("Removing", appDefault)
    utils.move(appDefault, appDefaultOld)
    log.summary("Placing new default in", appDefault)
    unzipFile(appHome+"/upgrade/default.zip", appHome)
    if utils.osname() != "nt":
       sysExpandedCommand(config, "chmod -R 755 /opt/java/openjdk/bin", config["JAVA_HOME"])
       sysExpandedCommand(config, "chmod -R 755 /opt/java/openjdk/jre/bin", config["JAVA_HOME"])

    if config["SERVER_MODE"] != "EDM":
       try:
          utils.rmStuff(appDefault + "/oatentreports")
       except:
          pass
       utils.rmStuff(appDefault + "/conf/META-INF/edm-application.xml")
    else:
       utils.rmStuff(appDefault + "/conf/META-INF/application.xml")
       utils.move(appDefault + "/conf/META-INF/edm-application.xml", appDefault + "/conf/META-INF/application.xml")
    if config["SERVER_MODE"] == "EDM":
       utils.move(appDefault + "/lib/enterprise", appDefault + "/lib/edm")
    if config["SERVER_MODE"] == "CCS":
       utils.move(appDefault + "/lib/enterprise", appDefault + "/lib/ccs")
    if config["WS_TYPE"] == "WebSphere":
       shutil.copy2(appDefault + "/both/WEB-INF/lib/ojdbc7_g.jar", appDefault + "/both/WEB-INF/lib/ojdbc7.jar")
       utils.rmStuff(appDefault + "/lib/jms.jar")
       utils.rmStuff(appDefault + "/both/WEB-INF/lib/bcprov-jdk13-132.jar")

def reCreateDefault():
    appDefault = appHome+"/default"
    if os.path.isdir(appDefault):
        log.summary("Removing", appDefault)
        try:
            utils.rmStuff(appDefault)
        except (os.error), why:
            utils.die("Can't clean default\n", str(why))

    log.summary("Preparing", appDefault)
    os.mkdir(appDefault)

    utils.copyStuff(appHome+"/tmp.deploy/upgrade/conf",       appDefault)
    for excl in confExcludes:
        utils.rmStuff(os.path.join(appDefault, "conf", excl), verbose=0)
    utils.copyStuff(webappHome+"/"+wsContext,    appDefault)
    utils.copyStuff(webappHome+"/raf.war", appDefault)
    utils.copyStuff(webappHome+"/oatedge", appDefault)
    utils.copyStuff(webappHome+"/oatentreports", appDefault)

    log.summary("hiding pre-processed output")
    hidePreProcessedFiles(appHome + "/default/conf")

def hidePreProcessedFiles(path):
    # deploy typically ignores files under "tmp" dirs
    for c in os.listdir(path):
        child = utils.pjoin(path, c)
        if os.path.isdir(child):
            hidePreProcessedFiles(child)
        elif os.path.exists(child + ".in"):
            utils.makePath(path + "/tmp")
            utils.move(child, utils.pjoin(path, "tmp", c))
    
def deployAll():
    # remove old contents of raf, axis
    removeOld()
    if version.oatedge < 4: editsForUnwarredRaf()

    # this string defines top-level precendence
    for g in "default ext/* local".split():
        for p in listPlugins(g):
            if deployPackage(unixpath(p)) == 0:
                log.summary("FATAL Error in deploying \"" + p +"\"")
                return

def editsForUnwarredRaf():
    # NOTE: ideally, sed of context.xml would be part of prepareDefaults, but
    # breaks install unless unwar raf at same time.
    try:
        filename = webappHome + "/context.xml"
        text = utils.readFile(filename)
        text = re.sub("raf\.war", "raf", text)
        utils.writeFile(filename, text, "wb")
    except (IOError, os.error), why:
        log.error("context.xml edit failed:", str(why))

def removeOld():
    # should we provide option to move them elsewhere?
    if not os.path.exists(appHome+"/default"):
        utils.die("./default does not exist.\n"
                  "Run prepareDefaults first.")

    try:
        utils.rmStuff(pjoin(pjoin(appHome, "conf"), "metadata"))

        if doAction["classes"]:
            utils.rmStuff(pjoin(appHome, "classes"))
        if doAction["axis"]:
            utils.rmStuff(pjoin(webappHome, wsContext))
        if doAction["ui"]:
            utils.rmStuff(pjoin(webappHome, uidir()))
        if doAction["oatentreports"]:
	    if config["SERVER_MODE"] == "EDM":
	       utils.rmStuff(pjoin(webappHome, "oatentreports") )

    except (os.error), why:
        utils.die("Can't clean webapps\n", str(why))

def listPlugins(pattern):
    # Run the glob and exclude exploded .oars
    raw = glob.glob(pjoin(appHome, pattern))
    a = []
    for p in raw:
        if isdir(p):
            a.append(p)
        elif suffix(p) == "oar" and raw.count(dropSuffix(p)) == 0:
            a.append(p)
    return utils.sorted(a)

def prodName():
    return "oatedge"

def uidir():
    return "oatedge"

# ---------------------- package deployer ----------------------

def deployPackage(p):
    if not exists(p):
        log.error("No such package:", p)
    elif suffix(p) == "oar":
        log.summary("Unzipping", p)
        dest = utils.childOfDir(dropSuffix(p), appTmpdir())
        utils.rmStuff(dest, verbose=0)
        if unzipFile(p, dest) == 0:
           return 0
        return deployPackage(dest)
    elif isdir(p):
        log.summary("Deploying", p)
        deployer = PackageDeployer(config, p, doAction)
        if doAction["custom"]: deployer.customHook()
        return deployer.run()
    else:
        log.error("Not an oarfile:", p)
        return 0


class PackageDeployer(AbstractDeployer):
    """Copy and merge files from exploded directory

    Exported as 'deployer' to custom deploy scripts"""

    axis = ui = conf = classes = sql = sql_ent = sql_site = sql_star = lib = bin = oss = oatentreports = nano =  EdgeMQsetup = ext = mobile = 0 # set via __dict__

    def __init__(self, theConfig, srcDir, actions):
        AbstractDeployer.__init__(self, theConfig, srcDir, "oar-deploy.py")
        self.packageName = self._getPackageName(srcDir)
        self.__dict__.update(actions)

    def run(self):
        if not self.dorun: return
        self.dorun = 0

        p = self.dir
        getVersionFromProp()
        confDir = config["CONF_DIR"]
        if onFederation == 1:
            config["CONF_DIR"] = "$OAT.conf.dir$"
            config["LOG_DIR"] = "$OAT.log.dir$"
            self.sql = self.sql_site = self.sql_ent = self.sql_star = 0
        if self.bin and deployStdDir(p+"/bin",  appHome+"/bin") == 0:
             log.summary ("************Error in bin deploy. Check the logs************")
             return 0
        if self.lib and deployStdDir(p+"/lib",  appHome+"/lib") == 0:
             log.summary ("************Error in lib deploy. Check the logs************")
             return 0
        if self.oss and deployStdDir(p+"/oss",  appHome+"/oss") == 0:
             log.summary ("************Error in oss deploy. Check the logs************")
             return 0
        if self.lib and deployStdDir(p+"/both/WEB-INF/lib",  appHome+"/lib") == 0:
             log.summary ("************Error in lib deploy w.r.t. both/WEB-INF/lib. Check the logs************")
             return 0
        if self.classes and deployStdDir(p+"/both/WEB-INF/classes",  appHome+"/classes") == 0:
             log.summary ("************Error in classes deploy w.r.t. both/WEB-INF/classes. Check the logs************")
             return 0
        if self.lib and deployStdDir(p+"/"+uidir()+"/applets",  appHome+"/lib/applet") == 0:
             log.summary ("************Error in lib/applet deploy. Check the logs************")
             return 0
        if self.lib and deployStdDir(p+"/lib",  webappHome+"/"+wsContext+"/WEB-INF/lib", recursive=0) == 0:
             log.summary ("************Error in "+wsContext+"/WEB-INF/lib deploy w.r.t. lib/. Check the logs************")
             return 0

        if self.axis and deployStdDir(p+"/both", webappHome+"/"+wsContext) == 0:
             log.summary ("************Error in "+wsContext+" deploy w.r.t. both/. Check the logs************")
             return 0
        if self.ui and  deployStdDir(p+"/both", webappHome+"/"+uidir()) == 0:
             log.summary ("************Error in "+uidir()+" deploy w.r.t. both/. Check the logs************")
             return 0
        if self.mobile and deployStdDir(p+"/mobile", appHome+"/mobile") == 0:
             log.summary ("************Error in mobile deploy. Check the logs************")
             return 0
        if self.axis and deployWebapp(p+"/axis",     webappHome+"/"+wsContext) == 0:
             log.summary ("************Error in axis deploy. Check the logs************")
             return 0
        if self.ui and deployWebapp(p+"/"+uidir(), webappHome+"/"+uidir()) == 0:
             log.summary ("************Error in "+uidir()+" deploy. Check the logs************")
             return 0
			 
        if config["SERVER_MODE"] == "EDM":
	   if deployWebapp(p+"/oatentreports", webappHome+"/oatentreports") == 0:
              log.summary ("************Error in oatentreports deploy. Check the logs************")
              return 0



        if self.classes and deployStdDir(p+"/classes",  appHome+"/classes") == 0:
             log.summary ("************Error in classes deploy. Check the logs************")
             return 0
        if self.conf and deployStdDir(p+"/conf",  confDir) == 0:
             log.summary ("************Error in conf deploy. Check the logs************")
             return 0
        if self.nano and deployStdDir(p+"/nano",  appHome+"/nano") == 0:
             log.summary ("************Error in nano deploy. Check the logs************")
             return 0
        if self.EdgeMQsetup and deployStdDir(p+"/EdgeMQsetup",  appHome+"/EdgeMQsetup") == 0:
             log.summary ("************Error in EdgeMQsetup deploy. Check the logs************")
             return 0
        if ofsUpgrade == 1 and self.ext and deployStdDir(p+"/ext",  appHome+"/ext") == 0:
             log.summary ("************Error in ext deploy. Check the logs************")
             return 0
        if self.conf and deployStdDir(p+"/mconf", confDir, mconfStyle=1) == 0: # deprecated
             log.summary ("************Error in conf deploy. Check the logs************")
             return 0
        if self.sql :
            if sqlDeploy(config, p+"/sql", self.packageName, forceRedeployLastSqlVersion) == 0:
                log.summary ("************Error in sql deploy. Check the logs************")
                return 0
        if self.sql_site and config["SERVER_MODE"] == "SITE":
            if sqlDeploy(config, p+"/sql_site", self.packageName, forceRedeployLastSqlVersion) == 0:
                log.summary ("************Error in sql_site deploy. Check the logs************")
                return 0
        if self.sql_ent and (config["SERVER_MODE"] == "EDM" or config["SERVER_MODE"] == "CCS") :     
            if sqlDeploy(config, p+"/sql_ent", self.packageName, forceRedeployLastSqlVersion) == 0:
                log.summary ("************Error in sql_ent deploy. Check the logs************")
                return 0
        if isdir(self.dir+"/sql_star") and config["SERVER_MODE"] == "EDM" :
            db_passwd = config["DB_PASSWORD"]
            db_name = config["DB_NAME"]
            db_user = config["DB_USER"]
            db_host = config["DB_HOST"]
            db_port = config["DB_PORT"]
            config["DB_PASSWORD"] = config["STAR_DB_PASSWORD"]
            config["DB_NAME"] = config["STAR_DB_NAME"]
            config["DB_USER"] = config["STAR_DB_USER"]
            config["DB_HOST"] = config["STAR_DB_HOST"]
            config["DB_PORT"] = config["STAR_DB_PORT"]
            if sqlDeploy(config, p+"/sql_star", self.packageName, forceRedeployLastSqlVersion) == 0:
                log.summary ("************Error in sql_star deploy. Check the logs************")
                return 0
            config["DB_PASSWORD"] = db_passwd
            config["DB_NAME"] = db_name
            config["DB_USER"] = db_user
            config["DB_HOST"] = db_host
            config["DB_PORT"] = db_port
        config["CONF_DIR"] = confDir
        return 1

    def _getPackageName(self, p):
        versionFile = p + "/version.txt"
        pname = os.path.basename(p)
        if exists(versionFile):
            props = utils.parseProperties(utils.readlines(versionFile))
            pname += "-%s-%s" % (props.get("PACKAGE", ""),
                                 props.get("VERSION", ""))
        return pname

# ---------------------- webapp ----------------------

def getVersionFromProp():
      versionFile = config["CONF_DIR"] + "/oatedge_version.properties"
      version = ""
      if exists(versionFile):
           props = utils.parseDotedProperties(utils.readlines(versionFile))
           log.detail("version property:",props)
           version = props.get("oatedge.version", "")
      else:
           versionFile = config["CONF_DIR"] + "/axiom_version.properties"
           if exists(versionFile):
                props = utils.parseDotedProperties(utils.readlines(versionFile))
                log.detail("version property:",props)
                version = props.get("axiom.version", "")
      log.detail("version from property file:",version)
      config["VERSION_PROP"] = re.sub(r"\.",r"",version)
      if (int(config["VERSION_PROP"]) < 100):
          config["VERSION_PROP"] = config["VERSION_PROP"] +"0"
      log.detail("version from property file after conversion:",config["VERSION_PROP"])

def deployWebapp(src, destdir):
    if isdir(src):
        if deployStdDir(src, destdir) == 0:
              return 0
    else:
        warfile = src+".war"
        if isfile(warfile):
            log.summary("  unwarring", warfile)
            dest = utils.childOfDir(src, destdir)
            unzipFile(warfile, dest)
    return 1


# ---------------------- std deploy ----------------------

def deployStdDirAtSameLocation(src, verbose=1, mconfStyle=0):
    """Copy files or dirs to dest dir, overwriting, preprocessing, and merging.

    Note that dest is final dir, not parent.

    tmp subdirectories are ignored."""

    if not exists(src):
        return
    if (basename(src) == "tmp"): # byproduct of merge-preproc or original setup
        return    
    if verbose:
        log.summary("  merging", src)

    if isdir(src): 
        names = os.listdir(src)
        for name in names:
            srcChild  = pjoin(src, name)
            deployStdDirAtSameLocation(srcChild, verbose=0, mconfStyle=mconfStyle)
    else:
        try:
            deployStdFileAtSameLocation(src)
        except (IOError, os.error), why:
            log.error("Can't merge %s to %s: %s" % (`src`, `dest`, str(why)))

def deployStdFileAtSameLocation(srcname):
    """Copy or merge file, possibly with preprocessing
    
    srcname and destname should have same suffixes.
    .m and .in will be dropped from dest"""

    if endsWith(srcname, ".m.in") or endsWith(srcname, ".in.m"):
        replaceAndMergeFile(srcname, dropSuffix(dropSuffix(srcname)))
    elif endsWith(srcname, ".in"):
        replaceConfigVars(config, srcname, dropSuffix(srcname))
    elif endsWith(srcname, ".m"):
        mergeFile(srcname, dropSuffix(srcname))

def deployStdDir(src, dest, verbose=1, mconfStyle=0, recursive=1):
    """Copy files or dirs to dest dir, overwriting, preprocessing, and merging.

    Note that dest is final dir, not parent.

    tmp subdirectories are ignored."""

    if not exists(src):
        return 1
    if (basename(src) == "tmp"): # byproduct of merge-preproc or original setup
        return 1
    if verbose:
        log.summary("  merging", src)

    if isdir(src): 
        if endsWith(src, ".remove"):
           if isdir(dropSuffix(dest)):
              log.summary("removing folder ",dropSuffix(dest))
	      utils.rmStuff(dropSuffix(dest))       
        else:
            names = utils.dirListFilt(src)
            utils.makePath(dest)
            for name in names:
                srcChild  = pjoin(src, name)
                destChild = pjoin(dest, name)
                if (recursive == 0 and isdir(srcChild)):
                    continue
                if deployStdDir(srcChild, destChild, verbose=0, mconfStyle=mconfStyle) == 0:
                    return 0
    else:
        try:
            if mconfStyle: # deprecated
                deployMconfFile(src, dest)
            else:
                deployStdFile(src, dest)
        except (IOError, os.error), why:
            log.error("Can't merge %s to %s: %s" % (`src`, `dest`, str(why)))
            return 0
    return 1

def deployStdFile(srcname, destname):
    """Copy or merge file, possibly with preprocessing
    
    srcname and destname should have same suffixes.
    .m and .in will be dropped from dest"""

    if endsWith(srcname, ".m.in") or endsWith(srcname, ".in.m"):
        replaceAndMergeFile(srcname, dropSuffix(dropSuffix(destname)))
    elif endsWith(srcname, ".*\.in\.m\.[0-9][0-9]$",1) or endsWith(srcname, ".*\.m\.in\.[0-9][0-9]$",1):
        replaceAndMergeFile(srcname, dropSuffix(dropSuffix(dropSuffix(destname))))
    elif endsWith(srcname, ".in"):
        replaceConfigVars(config, srcname, dropSuffix(destname))
        if ofsUpgrade == 1 or onFederation == 1:
           shutil.copy2(srcname, destname)
    elif endsWith(srcname, ".m"):
        mergeFile(srcname, dropSuffix(destname))
    elif endsWith(srcname, ".*\.m\.[0-9][0-9]$",1):
        mergeFile(srcname, dropSuffix(dropSuffix(destname)))
    elif endsWith(srcname, ".remove"):
         if os.path.isfile(dropSuffix(destname)):
           log.summary("removing file ",dropSuffix(destname))
	   utils.rmStuff(dropSuffix(destname))       
    elif endsWith(srcname, "$remove_star_star$"):
         if isdir(dirname(destname)):
           log.summary("removing all files from ",dirname(destname))
           fileNames = os.listdir(dirname(destname))
           for name in fileNames:
              if os.path.isfile(pjoin(dirname(destname), name)):
	          utils.rmStuff(pjoin(dirname(destname), name))       
    else:
        shutil.copy2(srcname, destname)

def deployMconfFile(srcname, destname):
    """Deprecated; use conf/*.m instead"""
    if endsWith(srcname, ".in"):
        replaceAndMergeFile(srcname, dropSuffix(destname))
    else:
        mergeFile(srcname, destname)

def replaceAndMergeFile(srcname, destname):
    """srcname should end in .m.in (or .in.m);  destname should not.
    "in.m" is prefered to "m.in" so tmp file will says .m, not .in"""

    tmpdir = dirname(srcname)+"/tmp"
    utils.makePath(tmpdir)
    
    tmpfile = pjoin(tmpdir, basename(dropSuffix(srcname))) 
    replaceConfigVars(config, srcname, tmpfile)
    
    mergeFile(tmpfile, destname) 

def mergeFile(src, dest):
    """srcname should have .m (except mconf/*), destname should not

    Empty dest will be created if missing"""

    if suffix(dest) == "properties":
        mergeProperties(src, dest)
    elif suffix(dest) == "xml" or endsWith(dest, ".xml.template"):
        mergeXml(src, dest)
    else:
        utils.fileAppend(src, dest)

# ---------------------- other helpers ----------------------

def unzipFile(zipfile, dest):
    utils.makePath(dest)
    if sysExpandedCommand(config, "/opt/java/openjdk/bin/jar -xf "+zipfile, dest) != 0:
        return 0
    return 1

def appTmpdir():
    """If necessary, create appHome/tmp"""

    # tempfile.gettempdir() not so reliable for jython
    tmpdir = appHome + "/tmp.deploy"
    utils.makePath(tmpdir)
    return tmpdir

# ---------------------- do it ----------------------

#-----MV-7399: added sys.exit to prevent jython process getting into hung state
if __name__ == "__main__":
    sys.exit(main())

