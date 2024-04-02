# $Source: /usr/local/cvs/scripts/deploy/bin/configVars.py,v $
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
# $Id: configVars.py,v 1.97.4.1 2017/05/11 19:23:23 jfang Exp $
"""
Provides dictionary of configuration properties.

Typicall loads ../deploy.config or ../configure.properties.
"""

import sys, re, os
import utils
import log
import java
import org
import com


# refactor this by replacing it with a Borg (5.22 of Py Cookbook)?
# These are variables used by system and deploy files
# Some will be derived, so are not expected in deploy.properties
"""
CLIENT_CLASSPATH
"""
requiredVars = """
    APP_HOME
    ARG_FORMAT
    BIN_DIR
    CATALINA_HOME
    CATALINA_HOME2
    CATALINA_HOME_UX_FORMAT
    CATALINA_BASE_UX_FORMAT
    CLASSPATH
    COMMENT
    NANO_DIR
    CONF_DIR
    MOBILE_DIR
    CONF_DIR_URL
    DB_CONN_CHECK_LEVEL
    DB_CONN_TEST_STMT
    DB_DRIVER
    DB_HOST
    DB_NAME
    DB_PASSWORD
    DB_PASSWORD_BIRT_ENCRYPTED
    DB_PASSWORD_ENCRYPTED
    DB_SERVICE
    DB_PORT
    DB_TYPE
    DB_URL
    DB_USER
    SERVICE_DEPENDENCY
    ENABLE_JMS
    ENABLE_I18N
    INSTALL_DIR
    IS_MANAGED_BY_SELF
    JAVA
    JAVA_HOME
    JAVA_HOME2
    JAVA_HOME_UX_FORMAT
    JDBC_PREFIX
    JMS_CONNECTION_FACTORY
    JMS_PASSWORD
    JMS_PROVIDER_URL
    JMS_QUEUE_NAME
    JMS_USER_NAME
    JMS_AGENT_PROVIDER_SERVICE
    JAVA_XMX
    LIB_DIR
    LOG_DIR
    LOGIN_EVENT
    OATEDGE_NAME
    OATEDGE_PORT
    ODS_DB_URL
    ODS_DIRECT_DB_URL
    ODS_DB_PASSWORD
    ODS_DB_NAME
    ODS_DB_USER
    ODS_DB_USER_CAPS
    ODS_DB_HOST
    ODS_DB_PORT
    RAMPART_MODULE
    SAP_AII_USER
    SAP_AII_PASSWORD
    SCRIPT_EXT
    SENDER_ADDR_FOR_ACCOUNT_CHANGES
    SENDER_ADDR_FOR_ALERTS
    SEP
    SERVER_MODE_NAME
    SLASH
    SMTP_HOST
    SOAP_URL
    SOAP_PORT
    SOAP_ADMIN_URL
    SOURCE_DIR
    SQLSVC_NAME
    SSL_ENABLE
    SSL_HOST_NAME
    SSL_PORT
    START_UP
    SW_HIERARCHY_POSITION
    STAGE_DB_PASSWORD
    STAGE_DB_NAME
    STAGE_DB_USER
    STAGE_DB_USER_CAPS   
    STAGE_DB_HOST
    STAGE_DB_PORT
    STAR_DB_PASSWORD
    STAR_DB_DOMAIN_NAME
    STAR_DB_NAME
    STAR_DB_USER
    STAR_DB_USER_CAPS
    STAR_DB_HOST
    STAR_DB_PORT
    STAGE_DB_URL
    STAR_DB_URL
    STAGE_DIRECT_DB_URL
    STAR_DIRECT_DB_URL
    START_LINE
    TOMCAT_INSTALL_DIR
    USER_AUTH_PASSWD_CACHE
    USER_OAT_USER_GROUP_NAMES
    USER_MANAGEMENT_EXTERNAL_SERVICE
    USER_MANAGEMENT_LOCAL_SERVICE
    USER_MANAGEMENT_EXT_SITE_SERVICE
    USER_MANAGEMENT_SITE_SERVICE
    USER_MANAGEMENT_SERVICE
    USER_IS_EXTERNAL_AUTH_MODE
    USER_ENT_SOAP_URL
    VERSION_PROP
    WAS_ADMIN_GROUPS
    WAS_ADMIN_USER_NAME
    WAS_ADMIN_USER_PASSWD
    WAS_LOGIN_ENABLED
    WEBAPP_HOME
    WS_TYPE
    WASSVC_NAME
    WAS_APPSERVER
    WAS_BIN_DIR
    WAS_HOME
    WAS_CONNTYPE_STRING
    """.split()

def deployInit(logDir=None, configFile=None):
    """Opens log files and loads config file."""
    if not logDir:
        if os.path.exists(scriptParent() + "/../axiom/conf"):
            logDir = _unixNormpath(utils.pjoin(scriptParent(), "../../setup"))
        else:
            logDir = _unixNormpath(utils.pjoin(scriptParent(), "../setup"))
    log.init(logDir)
    config = load(configFile)
    printDict(config)
    return config

def load(filename=None):
    """Returns dictionary of key=value pairs read from filename.

    Loads ../deploy.config or ../configure.properties by default.

    Will infer some vars if not set, and complain if others not set."""

    if not filename: 
        default1 = scriptParent()+"/deploy.properties"
        default2 = scriptParent()+"/configure.properties"
        if os.path.exists(default1):
            filename = default1
        else:
            filename = default2

    log.detail("loading config from", filename)
    config = loadDictFromFile(filename)
    stripQuotes(config)
    fillMissingConfig(config)
    checkConfig(config)
    return config 

def stripQuotes(config):
    regex = re.compile("^['\"](.*)['\"]$")
    for k in config.keys():
        config[k] = regex.sub(r"\1", config[k])

def fillMissingConfig(config):
    """Sets missing config vars when it can."""

    config.setdefault("APP_HOME", scriptParent())
    config.setdefault("VERSION_PROP", "")
    config.setdefault("JAVA_XMS", "1024m")
    config.setdefault("JAVA_XMX", "1024m")
    config.setdefault("JMS_AGENT_PROVIDER_SERVICE", "ActiveMQJMSAgent")
    config.setdefault("WAS_CONNTYPE_STRING", "")
    config.setdefault("WAS_ADMIN_USER_NAME", "")
    config.setdefault("WAS_ADMIN_USER_PASSWD", "")
    config.setdefault("LOGIN_EVENT", "GOTO_LOGIN_EVENT")
    config.setdefault("WAS_LOGIN_ENABLED", "false")
    config.setdefault("WAS_ADMIN_GROUPS", "")
    config.setdefault("USER_OAT_USER_GROUP_NAMES", "")

    if config["SSL_ENABLE"] == "false":
        config["SSL_PORT"]=""

    if config["WAS_LOGIN_ENABLED"] == "true":
        config["LOGIN_EVENT"]="WAS_LOGIN_EVENT"

    if config["WAS_ADMIN_USER_NAME"] == "" or config["WAS_ADMIN_USER_NAME"] == None:
        config["WAS_ADMIN_USER_PASSWD"]=""

    appHome = config["APP_HOME"]
    dbType = config["DB_TYPE"].upper()
    if _unixNormpath(appHome) != scriptParent():
        if not config.get("PERMIT_REMOTE_APP_HOME", 0):
            utils.die("APP_HOME is not the same as script parent:",
                      appHome, "vs", scriptParent())

    if not config.has_key("DM_DATA_COMPRESSION_ENABLED"):
        config.setdefault("DM_DATA_COMPRESSION_ENABLED", "true")
    if not config.has_key("DM_PUSH_MODE"):
        config.setdefault("DM_PUSH_MODE", "yes")
    if not config.has_key("DM_TRANSPORT_SIZE"):
        config.setdefault("DM_TRANSPORT_SIZE", "100000")
    if not config.has_key("DM_WAIT_TIME"):
        config.setdefault("DM_WAIT_TIME", "10")
    if not config.has_key("DM_SCHDULE_TIME"):
        config.setdefault("DM_SCHDULE_TIME", "60")
    if not config.has_key("ORACLE_DB_CONN_TEST_STMT"):
        config.setdefault("ORACLE_DB_CONN_TEST_STMT", "SELECT 1 FROM DUAL")
    if not config.has_key("POSTGRES_DB_CONN_TEST_STMT"):
        config.setdefault("POSTGRES_DB_CONN_TEST_STMT", "SELECT 1")
    if not config.has_key("SQLSERVER_DB_CONN_TEST_STMT"):
        config.setdefault("SQLSERVER_DB_CONN_TEST_STMT", "SELECT 1")
    if not config.has_key("DB2_DB_CONN_TEST_STMT"):
        config.setdefault("DB2_DB_CONN_TEST_STMT", "SELECT 1 FROM SYSIBM.SYSDUMMY1")
    if not config.has_key("ORACLE_DB_CONN_CHECK_LEVEL"):
        config.setdefault("ORACLE_DB_CONN_CHECK_LEVEL", "2")
    if not config.has_key("POSTGRES_DB_CONN_CHECK_LEVEL"):
        config.setdefault("POSTGRES_DB_CONN_CHECK_LEVEL", "2")
    if not config.has_key("SQLSERVER_DB_CONN_CHECK_LEVEL"):
        config.setdefault("SQLSERVER_DB_CONN_CHECK_LEVEL", "2")
    if not config.has_key("DB2_DB_CONN_CHECK_LEVEL"):
        config.setdefault("DB2_DB_CONN_CHECK_LEVEL", "2")
    if os.path.exists(appHome + "/../axiom/conf"):
        installHome = _unixNormpath(utils.pjoin(appHome, "../.."))
        config.setdefault("STAGE_DB_USER",     config["%s_STAGE_DB_USER" % dbType])
        config["STAGE_DB_USER_CAPS"] = config["STAGE_DB_USER"].upper()
        config.setdefault("STAGE_DB_PASSWORD", config["%s_STAGE_DB_PASSWORD" % dbType])
        config.setdefault("ODS_DB_USER",     config["%s_ODS_DB_USER" % dbType])
        config["ODS_DB_USER_CAPS"] = config["ODS_DB_USER"].upper()
        config.setdefault("ODS_DB_PASSWORD", config["%s_ODS_DB_PASSWORD" % dbType])
        config.setdefault("STAR_DB_USER",     config["%s_STAR_DB_USER" % dbType])
        config["STAR_DB_USER_CAPS"] = config["STAR_DB_USER"].upper()
        config.setdefault("STAR_DB_PASSWORD", config["%s_STAR_DB_PASSWORD" % dbType])
        config.setdefault("OATEDGE_PORT", "")
        for ak in utils.sorted(config.keys()):
            if re.search ('ADAPTER_', ak) != None:
                config[ak] =  _unixNormpath(config[ak])
    else:
        installHome = _unixNormpath(utils.pjoin(appHome, ".."))
        config.setdefault("STAGE_DB_PASSWORD", "")
        config.setdefault("STAGE_DB_NAME", "")
        config.setdefault("STAGE_DB_USER", "")
        config.setdefault("STAGE_DB_HOST", "")
        config.setdefault("STAGE_DB_PORT", "")
        config.setdefault("ODS_DB_PASSWORD", "")
        config.setdefault("ODS_DB_NAME", "")
        config.setdefault("ODS_DB_USER", "")
        config.setdefault("ODS_DB_HOST", "")
        config.setdefault("ODS_DB_PORT", "")
        config.setdefault("STAR_DB_PASSWORD", "")
        config.setdefault("STAR_DB_NAME", "")
        config.setdefault("STAR_DB_USER", "")
        config.setdefault("STAR_DB_HOST", "")
        config.setdefault("STAR_DB_PORT", "")
        config.setdefault("DB_USER",     config["%s_DB_USER" % dbType])
        config.setdefault("DB_PASSWORD", config["%s_DB_PASSWORD" % dbType])
        config.setdefault("WEBAPP_PORT", config["OATEDGE_PORT"])
        config.setdefault("DB_CONN_TEST_STMT", config["%s_DB_CONN_TEST_STMT" % dbType])
        config.setdefault("DB_CONN_CHECK_LEVEL", config["%s_DB_CONN_CHECK_LEVEL" % dbType])
    ###
    # JIRA TWO-8728-if db type is oracle - Oracle10gDialect should be used as Oracle9Dialect is been deprecated
    ###
	if config["DB_TYPE"] == "db2":
	   config["HIBERNATE_DIALECT"] = "org.hibernate.dialect.DB2Dialect"
           config["KETTLE_DB_TYPE"] = "DB2"
        elif config["DB_TYPE"] == "sqlserver":
           config["HIBERNATE_DIALECT"] = "org.hibernate.dialect.SQLServerDialect"
           config["KETTLE_DB_TYPE"] = "MSSQL"
        elif config["DB_TYPE"] == "oracle":
  	   config["HIBERNATE_DIALECT"] = "org.hibernate.dialect.Oracle10gDialect"
           config["KETTLE_DB_TYPE"] = "ORACLE"
	
    
    config.setdefault("TOMCAT_INSTALL_DIR", "apache-tomcat-6.0.35")
    config.setdefault("CATALINA_HOME", config["INSTALL_DIR"]+"/"+config["TOMCAT_INSTALL_DIR"])
    config.setdefault("CATALINA_BASE", config["INSTALL_DIR"]+"/"+config["TOMCAT_INSTALL_DIR"])
    config.setdefault("CATALINA_HOME2", utils.replaceSingleSlashByDouble(config["CATALINA_HOME"]))

    if config.has_key("AXIOM_OWNER"):
        config["AXIOM_OWNER"] = utils.replaceSingleQuoteByDouble(config["AXIOM_OWNER"])

    ####
    # replaceing double back slash (\\) with single. Calling twice, bec need to replace \\\\ by \
    ####
    config["INSTALL_DIR"] = utils.replaceDoubleSlashBySingle(config["INSTALL_DIR"])
    config["INSTALL_DIR"] = utils.replaceDoubleSlashBySingle(config["INSTALL_DIR"])
    config["INSTALL_DIR"] = utils.syspath(config["INSTALL_DIR"])
    config.setdefault("INSTALL_DIR2", utils.replaceSingleSlashByDouble(config["INSTALL_DIR"]))
    if config.has_key("DB_HOST"):
        config["DB_HOST"] = utils.replaceDoubleSlashBySingle(config["DB_HOST"])
        config["DB_HOST"] = utils.replaceSingleSlashByDouble(config["DB_HOST"])
    if config.has_key("STAR_DB_HOST"):
        config["STAR_DB_HOST"] = utils.replaceDoubleSlashBySingle(config["STAR_DB_HOST"])
        config["STAR_DB_HOST"] = utils.replaceSingleSlashByDouble(config["STAR_DB_HOST"])
    if config.has_key("STAGE_DB_HOST"):
        config["STAGE_DB_HOST"] = utils.replaceDoubleSlashBySingle(config["STAGE_DB_HOST"])
        config["STAGE_DB_HOST"] = utils.replaceSingleSlashByDouble(config["STAGE_DB_HOST"])
    if config.has_key("ODS_DB_HOST"):
        config["ODS_DB_HOST"] = utils.replaceDoubleSlashBySingle(config["ODS_DB_HOST"])
        config["ODS_DB_HOST"] = utils.replaceSingleSlashByDouble(config["ODS_DB_HOST"])
    config.setdefault("JAVA_HOME",     installHome+"/jdk1.6.0")
    config.setdefault("JAVA_HOME2",    utils.replaceSingleSlashByDouble(config["JAVA_HOME"]))
    config.setdefault("DEPLOY_LOG_DIR", config["INSTALL_DIR"]+"/setup")
    config.setdefault("SOURCE_DIR", appHome)
    config.setdefault("BIN_DIR", appHome+"/bin")
    config.setdefault("LIB_DIR", appHome+"/lib")

    config.setdefault("JAVA",     config["JAVA_HOME"]+"/jdk1.6.0/bin/java")
    config["JAVA_HOME"] = utils.syspath(config["JAVA_HOME"])
    config["JAVA"] = utils.syspath(config["JAVA"])

    config.setdefault("LOG_DIR",       appHome+"/log")

    config.setdefault("NANO_DIR",  appHome+"/nano")
    config.setdefault("CONF_DIR",  appHome+"/conf")
    config.setdefault("MOBILE_DIR",  appHome+"/mobile")
    config.setdefault("CLASSPATH", config["CONF_DIR"])

    if utils.osname() == "nt":
        confDirUrlPrefix = "/"
        config.setdefault("COMMENT",  "@REM ")
        config.setdefault("SEP",  ";")
        config.setdefault("SLASH",  "\\")
        config.setdefault("ARG_FORMAT",  "%*")
        config.setdefault("START_LINE",  "@ECHO off")
        config.setdefault("SCRIPT_EXT", "bat")
    else:
        confDirUrlPrefix = ""
        config.setdefault("COMMENT",  "# ")
        config.setdefault("SEP",  ":")
        config.setdefault("SLASH",  "/")
        config.setdefault("ARG_FORMAT",  "$@")
        config.setdefault("START_LINE",  "#! /bin/bash")
        config.setdefault("SCRIPT_EXT", "sh")
    config.setdefault("CONF_DIR_URL",  confDirUrlPrefix + config["CONF_DIR"])

    try:
        jmsType = config.get("JMS_TYPE", "not set")
        if jmsType == "SonicMQ":
            jndiNamingFactory = "com.sonicsw.jndi.mfcontext.MFContextFactory"
            jndiProtocol = "tcp"
        elif jmsType == "Websphere":
            jndiNamingFactory = "com.ibm.websphere.naming.WsnInitialContextFactory"
            jndiProtocol = "iiop"
        else:
            jndiNamingFactory = "not set"
            jndiProtocol = "not set"
        config.setdefault("JNDI_NAMING_FACTORY",  jndiNamingFactory)
        url = "%s://%s:%s" % (jndiProtocol,
                              config["JMS_PROVIDER_URL_HOSTNAME"],
                              config["JMS_PROVIDER_URL_PORT"])
        config.setdefault("JNDI_NAMING_PROVIDER_URL", url)
    except KeyError, e:
        log.detail("*WARNING* Missing config var ", e)
        pass

    config.setdefault("DB_PORT",     "0")
    config.setdefault("DB_PASSWORD_ENCRYPTED", "false")
    try:
        if not config.has_key("ENABLE_I18N"):
            config.setdefault("ENABLE_I18N", "true")

        if not config.has_key("USER_MANAGEMENT_EXTERNAL_SERVICE"):
            config.setdefault("USER_MANAGEMENT_EXTERNAL_SERVICE", "UserManagementExternalService")

        if not config.has_key("USER_MANAGEMENT_LOCAL_SERVICE"):
            config.setdefault("USER_MANAGEMENT_LOCAL_SERVICE", "UserManagementLocalService")

        if not config.has_key("USER_MANAGEMENT_EXT_SITE_SERVICE"):
            config.setdefault("USER_MANAGEMENT_EXT_SITE_SERVICE", "UserManagementSiteService")

        if not config.has_key("USE_OAUTH2"):
            config ["USE_OAUTH2"] = "FALSE"

        if config["USER_AUTH_PASSWD_CACHE"] == "":
            config["USER_AUTH_PASSWD_CACHE"] = "false"

        if not config.has_key("SERVER_MODE"):
            config.setdefault("SERVER_MODE", "SITE")

        if not config.has_key("CCS_SERVER_ENABLED"):
            config.setdefault("CCS_SERVER_ENABLED", "FALSE")

        if not config.has_key("CCS_ENMS_SERVER_ENABLED"):
            config.setdefault("CCS_ENMS_SERVER_ENABLED", "FALSE")

        if not config.has_key("USER_IS_EXTERNAL_AUTH_MODE"):
            config.setdefault("USER_IS_EXTERNAL_AUTH_MODE", "FALSE")

        # Set the CCS_SERVER_ENABLED for EA based on CCS_ENMS_SERVER_ENABLED
        if  config["SERVER_MODE"] != "SITE":
            config["CCS_SERVER_ENABLED"]=config["CCS_ENMS_SERVER_ENABLED"]

        # Set the Product service based on the CCS_SERVER_ENABLED flag
        if config["CCS_SERVER_ENABLED"].upper() == "TRUE":
               config["PRODUCT_SERVICE"]="EnmsProductService"
        else:
               config["PRODUCT_SERVICE"]="DefaultProductService"

        if config["SERVER_MODE"] == "SITE":
            if config["CCS_SERVER_ENABLED"].upper() == "TRUE":
               # EA managed site
               config["USER_IS_EXTERNAL_AUTH_MODE"]="true"
               config["USER_MANAGEMENT_SITE_SERVICE"]=config["USER_MANAGEMENT_EXT_SITE_SERVICE"]
            else:
               # Standalone site
               config["USER_IS_EXTERNAL_AUTH_MODE"]="false"
               if config["USE_OAUTH2"].upper() == "TRUE":
                   config ["USER_MANAGEMENT_SITE_SERVICE"] = "UserManagementOAuthServices"
               else:
                   config["USER_MANAGEMENT_SITE_SERVICE"]=config["USER_MANAGEMENT_LOCAL_SERVICE"]
        else:
            # EA
            if config["USER_IS_EXTERNAL_AUTH_MODE"].upper() == "TRUE":
                if config["USE_OAUTH2"].upper() == "TRUE":
                    config["USER_MANAGEMENT_SERVICE"]="UserManagementOAuthServices"
                else:
                    config["USER_MANAGEMENT_SERVICE"]=config["USER_MANAGEMENT_EXTERNAL_SERVICE"]
            else:
                config["USER_IS_EXTERNAL_AUTH_MODE"]="false"
                config["USER_MANAGEMENT_SERVICE"]=config["USER_MANAGEMENT_LOCAL_SERVICE"]

        config.setdefault("DB_DRIVER",   config["%s_JDBC_DRIVER" % dbType])
	config.setdefault("STAR_DB_DRIVER",config["%s_JDBC_DRIVER" % dbType])
        config.setdefault("JDBC_PREFIX", config["%s_JDBC_PREFIX" % dbType])
	config.setdefault("STAR_JDBC_PREFIX",config["%s_JDBC_PREFIX" % dbType])
        config.setdefault("JDBC_DRIVER", config["%s_JDBC_DRIVER" % dbType])
	config["DB_DRIVER"] = config["JDBC_DRIVER"]
	config["ENTERPRISE_DB_TYPE"]=config["DB_TYPE"]
        config["ENTERPRISE_DB_DRIVER"]=config["DB_DRIVER"]
        config["ENTERPRISE_JDBC_PREFIX"]=config["JDBC_PREFIX"] 

        config.setdefault("RAMPART_MODULE", "<!-- <module ref=\"rampart\"/> -->")
        config.setdefault("WS_SECURITY", "false")
        config.setdefault("RMI_SECURITY", "false")
        config.setdefault("JMS_BROKER_SECURITY", "false")

        if config["WS_SECURITY"] == "true":
           config["RAMPART_MODULE"]="<module ref=\"rampart\"/>"

        if config["SSL_PORT"] != "":
           config["SOAP_SSL_PORT"]=str(int(config["SSL_PORT"])+1)
        
        if config["DM_SCHDULE_TIME"] == "" or config["DM_SCHDULE_TIME"] == None:
            config["DM_SCHDULE_TIME"] = "60"

	if config.has_key("STAR_DB_DOMAIN_NAME"):
           config["STAR_DB_DOMAIN_NAME"] = config["STAR_DB_DOMAIN_NAME"]
        config.setdefault("STAGE_DIRECT_DB_URL", {
            'DB2':  lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s:%s/%s" % (prefix, host, port, name),
            'ORACLE':    lambda prefix, host, port, name, enable_i18n, svcname: "%s:@//%s:%s/%s" % (prefix, host, port, svcname),
            'POSTGRES':  lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s/%s" % (prefix, host, name),
            'SQLSERVER': lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s:%s;DatabaseName=%s;SelectMethod=Direct;sendStringParametersAsUnicode=%s;" % (prefix, host, port, name, enable_i18n)
            }[dbType](config["JDBC_PREFIX"], config["STAGE_DB_HOST"], config["STAGE_DB_PORT"], config["STAGE_DB_NAME"], config["ENABLE_I18N"], config["DB_SERVICE"]))
        config.setdefault("ODS_DIRECT_DB_URL", {
            'DB2':  lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s:%s/%s" % (prefix, host, port, name),
            'ORACLE':    lambda prefix, host, port, name, enable_i18n, svcname: "%s:@//%s:%s/%s" % (prefix, host, port, svcname),
            'POSTGRES':  lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s/%s" % (prefix, host, name),
            'SQLSERVER': lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s:%s;DatabaseName=%s;SelectMethod=Direct;sendStringParametersAsUnicode=%s;" % (prefix, host, port, name, enable_i18n)
            }[dbType](config["JDBC_PREFIX"], config["ODS_DB_HOST"], config["ODS_DB_PORT"], config["ODS_DB_NAME"], config["ENABLE_I18N"], config["DB_SERVICE"]))
        config.setdefault("STAR_DIRECT_DB_URL", {
            'DB2':  lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s:%s/%s" % (prefix, host, port, name),
            'ORACLE':    lambda prefix, host, port, name, enable_i18n, svcname: "%s:@//%s:%s/%s" % (prefix, host, port, svcname),
            'POSTGRES':  lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s/%s" % (prefix, host, name),
            'SQLSERVER': lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s:%s;DatabaseName=%s;SelectMethod=Direct;sendStringParametersAsUnicode=%s;" % (prefix, host, port, name, enable_i18n)
            }[dbType](config["JDBC_PREFIX"], config["STAR_DB_HOST"], config["STAR_DB_PORT"], config["STAR_DB_NAME"], config["ENABLE_I18N"], config["STAR_DB_SERVICE"]))
        config.setdefault("STAGE_DB_URL", {
            'DB2':  lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s:%s/%s" % (prefix, host, port, name),
            'ORACLE':    lambda prefix, host, port, name, enable_i18n, svcname: "%s:@//%s:%s/%s" % (prefix, host, port, svcname),
            'POSTGRES':  lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s/%s" % (prefix, host, name),
            'SQLSERVER': lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s:%s;DatabaseName=%s;SelectMethod=cursor;sendStringParametersAsUnicode=%s;" % (prefix, host, port, name, enable_i18n)
            }[dbType](config["JDBC_PREFIX"], config["STAGE_DB_HOST"], config["STAGE_DB_PORT"], config["STAGE_DB_NAME"], config["ENABLE_I18N"], config["DB_SERVICE"]))
        config.setdefault("ODS_DB_URL", {
            'DB2':  lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s:%s/%s" % (prefix, host, port, name),
            'ORACLE':    lambda prefix, host, port, name, enable_i18n, svcname: "%s:@//%s:%s/%s" % (prefix, host, port, svcname),
            'POSTGRES':  lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s/%s" % (prefix, host, name),
            'SQLSERVER': lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s:%s;DatabaseName=%s;SelectMethod=Cursor;sendStringParametersAsUnicode=%s;" % (prefix, host, port, name, enable_i18n)
            }[dbType](config["JDBC_PREFIX"], config["ODS_DB_HOST"], config["ODS_DB_PORT"], config["ODS_DB_NAME"], config["ENABLE_I18N"], config["DB_SERVICE"]))
        config.setdefault("STAR_DB_URL", {
            'DB2':  lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s:%s/%s" % (prefix, host, port, name),
            'ORACLE':    lambda prefix, host, port, name, enable_i18n, svcname: "%s:@//%s:%s/%s" % (prefix, host, port, svcname),
            'POSTGRES':  lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s/%s" % (prefix, host, name),
            'SQLSERVER': lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s:%s;DatabaseName=%s;SelectMethod=cursor;sendStringParametersAsUnicode=%s;" % (prefix, host, port, name, enable_i18n)
            }[dbType](config["JDBC_PREFIX"], config["STAR_DB_HOST"], config["STAR_DB_PORT"], config["STAR_DB_NAME"], config["ENABLE_I18N"], config["STAR_DB_SERVICE"]))
        config.setdefault("DB_URL", {
            'DB2':  lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s:%s/%s" % (prefix, host, port, name),
            'ORACLE':    lambda prefix, host, port, name, enable_i18n, svcname: "%s:@//%s:%s/%s" % (prefix, host, port, svcname),
            'POSTGRES':  lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s/%s" % (prefix, host, name),
            'SQLSERVER': lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s:%s;DatabaseName=%s;SelectMethod=cursor;sendStringParametersAsUnicode=%s;" % (prefix, host, port, name, enable_i18n)
            }[dbType](config["JDBC_PREFIX"], config["DB_HOST"], config["DB_PORT"], config["DB_NAME"], config["ENABLE_I18N"], config["DB_SERVICE"]))
        config.setdefault("ENTERPRISE_DB_URL", {
            'DB2':  lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s:%s/%s" % (prefix, host, port, name),
            'ORACLE':    lambda prefix, host, port, name, enable_i18n, svcname: "%s:@//%s:%s/%s" % (prefix, host, port, svcname),
            'POSTGRES':  lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s/%s" % (prefix, host, name),
            'SQLSERVER': lambda prefix, host, port, name, enable_i18n, svcname: "%s://%s:%s;DatabaseName=%s;SelectMethod=cursor;sendStringParametersAsUnicode=%s;" % (prefix, host, port, name, enable_i18n)
            }[dbType](config["ENTERPRISE_JDBC_PREFIX"], config["ENTERPRISE_DB_HOST"], config["ENTERPRISE_DB_PORT"], config["ENTERPRISE_DB_NAME"], config["ENABLE_I18N"], config["ENTERPRISE_DB_SERVICE"]))
    except KeyError:
        log.detail("*WARNING* Missing config var ", e)
        pass

    try:
        config["INIT_SERVER_MODE"]=config["SERVER_MODE"]
	if config["INIT_SERVER_MODE"] == "SITE":
	   config["SMX_TELNET_PORT"]=config["SITE_SMX_TELNET_PORT"]
	   config["RMI_REG_PORT"]=config["SITE_RMI_REG_PORT"]
	   config["RMI_REG_PORT_MA"]=config["SITE_RMI_REG_PORT_MA"]
	   config["RMI_REG_PORT_WINSVC"]=config["SITE_RMI_REG_PORT_WINSVC"]
	   config["TYCO_NOTIF_PORT"]=config["SITE_TYCO_NOTIF_PORT"]
           config.setdefault("SERVER_MODE_NAME", "OATxpress")
        elif config["INIT_SERVER_MODE"] == "EDM":
	   config["SMX_TELNET_PORT"]=config["EDM_SMX_TELNET_PORT"]
	   config["RMI_REG_PORT"]=config["EDM_RMI_REG_PORT"]
	   config["RMI_REG_PORT_MA"]=config["EDM_RMI_REG_PORT_MA"]
	   config["RMI_REG_PORT_WINSVC"]=config["EDM_RMI_REG_PORT_WINSVC"]
	   config["TYCO_NOTIF_PORT"]=config["EDM_TYCO_NOTIF_PORT"]
           config.setdefault("SERVER_MODE_NAME", "OAT Enterprise Data Manager")
        if config["INIT_SERVER_MODE"] == "CCS":
           #config["SERVER_MODE"]="EDM"
           #config["ENTERPRISE_DB_NAME"]=config["DB_NAME"]
	   config["SMX_TELNET_PORT"]=config["CCS_SMX_TELNET_PORT"]
	   config["RMI_REG_PORT"]=config["CCS_RMI_REG_PORT"]
	   config["RMI_REG_PORT_MA"]=config["CCS_RMI_REG_PORT_MA"]
	   config["RMI_REG_PORT_WINSVC"]=config["CCS_RMI_REG_PORT_WINSVC"]
	   config["TYCO_NOTIF_PORT"]=config["CCS_TYCO_NOTIF_PORT"]
           config.setdefault("SERVER_MODE_NAME", "OAT Enterprise Administrator")
        config["server_mode"]=config["INIT_SERVER_MODE"].lower()
        config["OATEDGE_SERIAL_NUMBER"] = config["OATEDGE_SERIAL_NUMBER"].upper()        
        oatEdgeSerial = config["OATEDGE_SERIAL_NUMBER"]
        config.setdefault("OATEDGE_EPC", "FFFFFFFFFFFFFFF%sF%s"
                          % (oatEdgeSerial, oatEdgeSerial))
    except KeyError:        
        log.detail("*WARNING* Missing config var ", e)
        pass

    try:
        oatPort = config["OATEDGE_PORT"]
        webappPort = config["WEBAPP_PORT"]
        ccsServer = config["CCS_SERVER_HOST"]
        ccsServerPort = config["CCS_SERVER_PORT"]
        if not config.has_key("EDM_WS_CONTEXT"):
            config.setdefault("EDM_WS_CONTEXT", "axis")
        if not config.has_key("CCS_WS_CONTEXT"):
            config.setdefault("CCS_WS_CONTEXT", "axis")
        if not config.has_key("WS_CONTEXT"):
            config.setdefault("WS_CONTEXT", "axis")

        wsEntContext = config["CCS_WS_CONTEXT"]
        wsContext = config["WS_CONTEXT"]
        config.setdefault("USER_ENT_SOAP_URL", "http://%s:%s/%s/services"
                % (ccsServer, ccsServerPort, wsEntContext))
        config.setdefault("SOAP_URL", "http://localhost:%s/%s/services"
                % (webappPort, wsContext))
        config.setdefault("OATEDGE_SOAP_URL", "http://localhost:%s/%s/services"
                % (webappPort, wsContext))
        config.setdefault("SOAP_ADMIN_URL", "http://localhost:%s/%s/services/AxisServlet"
                % (webappPort, wsContext))
        config.setdefault("OATEDGE_SOAP_ADMIN_URL", "http://localhost:%s/%s/services/AxisServlet"
                % (webappPort, wsContext))

    except KeyError:
        log.detail("*WARNING* Missing config var ", e)
        pass

    config.setdefault("CMS_MGMT_STATION_SOAP_URL", "")
    config.setdefault("DATA_MIGRATION_HOST", "")
    config.setdefault("TIME_BETWEEN_DATA_MIGRATION", "")
    config.setdefault("TIME_BETWEEN_CONFIG_SYNC", "")
    config.setdefault("DB_PASSWORD_BIRT_ENCRYPTED","")

    config.setdefault("SQLSVC_NAME", "")
    config.setdefault("SERVICE_DEPENDENCY", "")

    # Service Name Change
    try:
        if config["SQLSVC_NAME"] != "" and config["SQLSVC_NAME"] != None:
            config["SERVICE_DEPENDENCY"] = com.oatsystems.devtool.ServiceMultiString.encodeDependOn(config["SQLSVC_NAME"])
    except:
        pass


    # Birt Password encryption 
    try:
        dbPassword = config["DB_PASSWORD"]
        if config["DB_PASSWORD_ENCRYPTED"] == "true":
            dbPassword = org.autoidcenter.util.EncryptionUtilities.decryptString(dbPassword)
        birtPassword = org.eclipse.birt.report.model.metadata.SimpleEncryptionHelper.getInstance().encrypt(dbPassword)
        config["DB_PASSWORD_BIRT_ENCRYPTED"] = birtPassword
    except:
        pass

    # ======== Note on UNIX vs Windows pathnames ======== 
    #
    # Unix pathnames are used for pathnames throughout the deployer for
    # readability.  This is fine for Python, Java, and the config files they
    # process, but not for .bat files.  Properties used by those files should
    # be distinct, and will be OS-sensitive.  All properties above this comment
    # use UNIX convention.  The following properties are OS-sensitive:
    
    config.setdefault("INSTALL_HOME", utils.syspath(installHome))
    config["JAVA_HOME"] = utils.syspath(config["JAVA_HOME"])
    config["CATALINA_HOME"] = utils.syspath(config["CATALINA_HOME"])
    config["CATALINA_BASE"] = utils.syspath(config["CATALINA_BASE"])
    config["CATALINA_HOME_UX_FORMAT"] = utils.unixpath(config["CATALINA_HOME"])
    config["CATALINA_BASE_UX_FORMAT"] = utils.unixpath(config["CATALINA_BASE"])
    config["SOURCE_DIR"] = utils.syspath(config["SOURCE_DIR"])

    config["CLASSPATH"] = utils.syspath(config["CONF_DIR"])
    config["JAVA_HOME"] = utils.syspath(config["JAVA_HOME"])
    config["JAVA_HOME_UX_FORMAT"] = utils.unixpath(config["JAVA_HOME"])
    config["JAVA"] = utils.syspath(config["JAVA_HOME"]+"/bin/java")
    config.setdefault("EGREP","egrep");
    config.setdefault("GREP","grep");
    config.setdefault("AWK","awk");
    config.setdefault("SED","sed");
    config.setdefault("LN_S","ln -s");
    config.setdefault("PSQL","psql");
    config.setdefault("CREATEDB","createdb");
    config.setdefault("DROPDB","dropdb");
    config.setdefault("CREATELANG","createlang");
    if not config.has_key("WAS_APPSERVER"):
          config.setdefault("WAS_APPSERVER", "server1")

    if not config.has_key("WAS_BIN_DIR"):
          config.setdefault("WAS_HOME", "")
          config.setdefault("WAS_BIN_DIR", "")
    else:
          config.setdefault("WAS_HOME", _unixNormpath(utils.pjoin(config["WAS_BIN_DIR"], "..")))

    if not config.has_key("OFS_ROOT"):
          config.setdefault("OFS_ROOT", config["INSTALL_HOME"])
          config.setdefault("OFS_ROOT2", config["INSTALL_DIR2"])
    if not config.has_key("HA_CONFIG"):
          config.setdefault("HA_CONFIG", "")
    if not config.has_key("WASSVC_NAME"):
          config.setdefault("WASSVC_NAME", "IBMWAS5Service - server1")

    try:
        config.setdefault("WEBAPP_HOME", config["CATALINA_BASE"]+"/webapps")
    except KeyError:
        log.detail("*WARNING* Missing config var ", e)
        pass


# for oatedge.in, would need
#  OATEDGE_SOAP_URL, OATEDGE_SOAP_ADMIN_URL


def checkConfig(config):
    """Checks for requiredVars (and fixes where it can) config"""
    for var in requiredVars:
        if not config.has_key(var):
            config.setdefault(var,"")

def scriptParent():
    """parent of whereever this script exists
    e.g. .../epc-is-3.0 or .../ofs    """
    return _unixNormpath(os.path.join(
        os.getcwd(),
        os.path.dirname(sys.argv[0]),
        ".."))

def _unixNormpath(path):
    return utils.unixpath(os.path.normpath(path))

def loadDictFromFile(filename):
    """Returns dict from file with lines of form 'name=value'."""
    try:
        config = utils.parseProperties(utils.readlines(filename))
        return config
    except Exception, why:
        utils.die("Can't load file: %s" % why)
        return []

def printDict(config):
    for k in utils.sorted(config.keys()):
        if re.search ('PASSW', k) == None:
             log.detail(k, "=", config[k])
        else:
             log.detail(k, "=", "*****")

def _test():
    if len(sys.argv[1:]) >= 1:
        config = load(sys.argv[1])
    else:
        config = load()
    printDict(config)

if __name__ == "__main__":
    _test()
