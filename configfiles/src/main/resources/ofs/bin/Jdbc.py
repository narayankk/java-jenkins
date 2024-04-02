# $Source: /usr/local/cvs/scripts/deploy/bin/Jdbc.py,v $
#
# Copyright (c) 1999-2006 OAT Systems, Inc.  All Rights Reserved.
#
# This software is the confidential and proprietary information
# (Confidential Information) of OAT Systems, Inc.  You shall not
# disclose or use Confidential Information without the express written
# agreement of OAT Systems, Inc.
#
#
# Author     : Krishnamoorthy Manickam
# Version $Id: Jdbc.py,v 1.35.4.9 2017/06/06 13:08:15 bnachimuthu Exp $
#

import sys, os, getopt, re
import java
import org
import com

import log, utils

# ---------------------- external methods ----------------------


def runSqlText(conn, text, dbtype):
    try:
        return conn.executeUpdates(text, dbtype)
    except Exception:
        log.exception()
        return 0

def runSqlTextInstall(conn, text, dbtype):
    try:
        return conn.executeUpdatesInstall(text, dbtype)
    except Exception:
        log.exception()
        return 0
		
def runSqlFile(conn, filename, dbtype):
    try:
        text = utils.readFile(filename)
        return runSqlText(conn, text, dbtype)
    except (IOError, os.error):
        log.exception()
        return 0

def runSqlFileInstall(conn, filename, dbtype):
    try:
        text = utils.readFile(filename)
        return runSqlTextInstall(conn, text, dbtype)
    except (IOError, os.error):
        log.exception()
        return 0

def executeSqlFile(conn, filename, dbtype):
    return conn.executeUpdates(utils.readFile(filename),dbtype)

def openDbConn(config):

    password = config["DB_PASSWORD"]
    if config["DB_PASSWORD_ENCRYPTED"] == "true":
        password = org.autoidcenter.util.EncryptionUtilities.decryptString(password)

    return openDbConnection(dbtype   = config["DB_TYPE"],
                            dbname   = config["DB_NAME"],
                            dbservice= config["DB_SERVICE"],
                            user     = config["DB_USER"],
                            password = password,
                            server   = config["DB_HOST"],
                            dburl	= config["DB_URL"],
                            port     = config.get("DB_PORT", 0),
                            driver   = config.get("JDBC_DRIVER", None))

def openMasterDbConn(config):

    password = config["DB_PASSWORD"]
    if config["DB_PASSWORD_ENCRYPTED"] == "true":
        password = org.autoidcenter.util.EncryptionUtilities.decryptString(password)

    return openDbConnection(dbtype   = config["DB_TYPE"],
                            dbname   = "master",
                            dbservice= config["DB_SERVICE"],
                            user     = config["DB_USER"],
                            password = password,
                            server   = config["DB_HOST"],
                            dburl	= config["MASTER_DB_URL"],
                            port     = config.get("DB_PORT", 0),
                            driver   = config.get("JDBC_DRIVER", None))							
							
def openStarDbConn(config):

    password = config["STAR_DB_PASSWORD"]
    if config["DB_PASSWORD_ENCRYPTED"] == "true":
        password = org.autoidcenter.util.EncryptionUtilities.decryptString(password)

    return openDbConnection(dbtype   = config["DB_TYPE"],
                            dbname   = config["STAR_DB_NAME"],
                            dbservice= config["STAR_DB_SERVICE"],
                            user     = config["STAR_DB_USER"],
                            password = password,
                            server   = config["STAR_DB_HOST"],
                            dburl	= config["DB_URL"],
                            port     = config.get("STAR_DB_PORT", 0),
                            driver   = config.get("JDBC_DRIVER", None))							

# ---------------------- JdbcConnection ----------------------

class JdbcConnection:

    ignoredCommands = ( 'exit' )

    def __init__( self, dbname, user, password, server, dburl, port=0, driver=None, dbservice=None ):
        
        self.dbname  = dbname
        self.dbservice = dbservice
        self.user    = user
        self.password= password
        self.server  = server
        self.port    = port
        self.dburl	 = dburl
		
        if driver:
            self.driver = driver
        else:
            self.driver = self.getDefaultDriver()

        self.jconn   = None

    def open(self):

        try:
		
            #log.detail("db url: ", self.getUrl())
            #log.detail("db driver ", self.driver)
            #log.detail("db user ", self.user)
            #log.detail("db passwd ", self.password)
            self.jconn = com.oatsystems.devtool.sqlmgr.DBConn.getDBConnection( self.driver, self.user, self.password, self.getUrl() )
        except Exception, why:
            raise DbError(why, "Connect failed: URL=%s, USER=%s, PASSWORD=%s, DRIVER=%s" 
                          % (self.getUrl(), self.user, "******", self.driver))


    def commit(self):
        if not self.jconn:
            return
        try:
            com.oatsystems.devtool.sqlmgr.DBConn.commit(self.jconn)
        except Exception:
            log.exception()

    def close(self):
        if not self.jconn:
            return
        if self.jconn == None:
            return
        try:
            com.oatsystems.devtool.sqlmgr.DBConn.commit(self.jconn)
            com.oatsystems.devtool.sqlmgr.DBConn.close(self.jconn)
        except Exception:
            log.exception()
        self.jconn = None

    def getUrl(self):
        raise AbstractMethodInvokedError, "getUrl"

    def getDefaultDriver(self):
        raise AbstractMethodInvokedError, "getDefaultDriver"

    def executeUpdate( self, sql, stmt=0 ):
        """Executes an SQL update statement."""
        log.detail("<<", sql, ">>")
        try:
            if not stmt:
                 com.oatsystems.devtool.sqlmgr.DBConn.executeStatement(self.jconn, sql)
            else:
                 com.oatsystems.devtool.sqlmgr.DBConn.executeSimpleStatement(self.jconn, sql)

            log.detail("SUCCESS")
            return 1
        except java.sql.SQLException, why:
            if sql.upper().startswith("DROP",0) == 1:
               log.detail("SQL WARNING: Error while dropping object")
               log.detail("SQL WARNING:" , why)
               log.exception()
               return 1
            log.detail("SQL Error:" , why)
            log.exception()
        except Exception, why:
            log.detail("SQL Error:" , why)
            log.exception()
        log.detail("Rolling back to pre-upgrade state...")
        #com.oatsystems.devtool.sqlmgr.DBConn.rollback(self.jconn)
        #com.oatsystems.devtool.sqlmgr.DBConn.close(self.jconn)
        return 0

    def executeUpdateInstall( self, sql, stmt=0 ):
        """Executes an SQL update statement."""
        #log.detail("<<", sql, ">>")
        try:
            if not stmt:
                 com.oatsystems.devtool.sqlmgr.DBConn.executeStatement(self.jconn, sql)
            else:
                 com.oatsystems.devtool.sqlmgr.DBConn.executeSimpleStatement(self.jconn, sql)

            #log.detail("SUCCESS")
            return 1
        except java.sql.SQLException, why:
            log.detail("<<", sql, ">>")              
            if sql.upper().startswith("DROP",0) == 1:
                log.detail("SQL WARNING: Error while dropping object")
                log.detail("SQL WARNING:" , why)
                log.exception()
                return 1
            log.detail("SQL Error:" , why)
            log.exception()
        except Exception, why:
            log.detail("<<", sql, ">>")
            log.detail("SQL Error:" , why)
            log.exception()
        log.detail("Rolling back to pre-upgrade state...")
        #com.oatsystems.devtool.sqlmgr.DBConn.rollback(self.jconn)
        #com.oatsystems.devtool.sqlmgr.DBConn.close(self.jconn)
        return 0



    def executeQuery( self, sql, quiet=0 ):
        """Executes an SQL query statement."""
        if not quiet:
            log.detail("<<", sql, ">>")
        try:
            results = com.oatsystems.devtool.sqlmgr.DBConn.executeQueryStatement(self.jconn, sql)
            if not quiet:
                log.detail("SUCCESS")
        except Exception, why:
            if not quiet:
                log.exception()
            log.detail("SQL Error:" , why)
            results = None
        return results

    def executeUpdates(self, text, dbtype):
        """Split text on ';', and executeUpdate on each."""
        sqlList = self._parseSqlText(text)

        for sqlStmt in sqlList:
            if self.ignoredCommands.count( sqlStmt ):
                log.detail("Ignoring statement <<%s>>\n" % sqlStmt)
                continue
            if sqlStmt.find("REPLACE TRIGGER") > 0:
                 if self.executeUpdate( sqlStmt + ";",1) == 0:
                      return 0
            elif sqlStmt.find("select ") == 0:
                 if self.executeQuery( sqlStmt ) == None:
                      return 0
            else:
                 if self.executeUpdate( sqlStmt ) == 0:
                      return 0
        return 1
		
    def executeUpdatesInstall(self, text, dbtype):
        """Split text on ';', and executeUpdate on each."""
        if dbtype == 'oracle':
			sqlList = self._parseOracleSqlText(text)
        elif dbtype == 'sqlserver':
			sqlList = self._parseSqlServerSqlText(text)

        for sqlStmt in sqlList:
			flag = 0
			if self.ignoredCommands.count( sqlStmt ):
				log.detail("Ignoring statement <<%s>>\n" % sqlStmt)
				continue
			pattern = re.compile(r'\s+')
			stmtwithoutspace = re.sub(pattern, '', sqlStmt[:40].upper() )
	
			if stmtwithoutspace.startswith("CREATEORREPLACEFUNCTION") | stmtwithoutspace.startswith("CREATEORREPLACEPROCEDURE") | stmtwithoutspace.startswith("CREATEORREPLACETRIGGER") :
				flag = 1
			if flag == 1:

				if self.executeUpdateInstall( sqlStmt + ";",1) == 0:
					continue
			elif sqlStmt.find("select ") == 0:
				if self.executeQuery( sqlStmt ) == None:
					continue
			else:
				if self.executeUpdateInstall( sqlStmt ) == 0:
					continue
        return 1
		
    def _parseSqlText (self, text):
        """Remove comments, and return list of statements"""
        list0 = text.split("\n")
        list1 = [ line for line in list0 if not line.startswith( "--" ) ]
        str1 = "\n".join( list1 )
        regex = re.compile(";\s*$", re.M)
        #####regex = re.compile("[\/\;]\s*$", re.M)
        # ignore empty lines
        return [ stmt.strip() for stmt in regex.split(str1) if stmt.strip() ]
		
    def _parseOracleSqlText (self, text):
		# remove the comments starting with /*
		text = re.sub(re.compile("/\*.*?\*/",re.DOTALL|re.MULTILINE ) ,"" ,text)
		list0 = text.split("\n")
		# remove the comments starting with --
		list1 = [ line for line in list0 if not line.startswith( "--" ) ]
		
		str1 = "\n".join( list1 )

		regex = re.compile(";\s*$", re.M)
		list2 = [ stmt.strip()+";"  for stmt in regex.split(str1) if stmt.strip() ]
		list3 = []
		list4 = []
		flag = 0
		newStmt = "";
		for stmt in list2:
			
			if stmt.startswith("/"):
				newlist = stmt.split("/")
				list3.append("/")
				list3.append(newlist[1].strip())
			else:
				list3.append(stmt.strip())
		for stmt in list3:
			pattern = re.compile(r'\s+')
			stmtwithoutspace = re.sub(pattern, '', stmt[:40].upper() )
			
			if stmtwithoutspace.startswith("CREATEORREPLACEFUNCTION") | stmtwithoutspace.startswith("CREATEORREPLACEPROCEDURE") | stmtwithoutspace.startswith("CREATEORREPLACETRIGGER") | stmtwithoutspace.startswith("DROPTRIGGER"):
				flag = 1
				newStmt = stmt
			elif stmtwithoutspace.startswith("/"):			
				if flag ==1:
					flag = 0
					if newStmt.strip():
						list4.append(newStmt.strip()[:-1])
						newStmt = "";
				else:
					list4.append(stmt[:-1])
			elif stmtwithoutspace.startswith("EXIT"):
				continue
			elif stmtwithoutspace.startswith("SETAUTOON"):
				continue
			else:
				if flag == 0:
					list4.append(stmt[:-1])
				else:
					newStmt = newStmt + "\n" + stmt
				
				
		#####regex = re.compile("[\/\;]\s*$", re.M)
		# ignore empty lines
		# return [ stmt.strip()  for stmt in regex.split(str1) if stmt.strip() ]
		return list4
		
    def _parseSqlServerSqlText (self, text):
		text = re.sub(re.compile("/\*.*?\*/",re.DOTALL|re.MULTILINE ) ,"" ,text)
		list0 = text.split("\n")
		# remove the comments starting with --
		list1 = [ line for line in list0 if not line.startswith( "--" ) ]
	
		# remove the comments starting with /*
		str1 = "\n".join( list1 )

		list2 = []
		list3 = []
		list4 = []
		stmt = ""
		flag = 0

		for line in list1:
			if line.startswith("GO") | line.startswith("go"):
				if flag == 0:
					flag = 1
					list3.append(stmt)
					stmt = ""
				elif flag == 1:	
					pattern = re.compile(r'\s+')
					stmtwithoutspace = re.sub(pattern, '', stmt[:40].upper() )
					if stmtwithoutspace.startswith("BEGIN") | stmtwithoutspace.startswith("CREATEFUNCTION") | stmtwithoutspace.startswith("CREATEPROCEDURE") | stmtwithoutspace.startswith("CREATETRIGGER"):
						stmt = stmt.replace(";","")
					list3.append(stmt)
					stmt = ""
			else:
				stmt = stmt + "\n" + line

		list3.append(stmt.strip())

		for stmt in list3:
			regex = re.compile(";\s*$", re.M)
			tempList = [s1.strip() for s1 in regex.split(stmt) if s1.strip()]
			for list in tempList:
				list4.append(list.strip())
		return list4



		
    def hasTable(self, table):
        try:
           rows = self.executeQuery("select count(*) from %s" % table, quiet=1)
           if rows == None:
               return 0
           else:
               return 1
        except Exception:
           return 0
        except java.sql.SQLException:
           return 0

# ---------------------- subclasses and factory ----------------------

class OracleConnection( JdbcConnection ):
    def getUrl(self):
        databaseurl = self.dburl
        if databaseurl.strip():
            log.detail("Database URL is not empty.")
            return databaseurl
        else:
            log.detail("Host name is not empty: hostname=" + self.server +", port="+ self.port+ ", url="+self.dburl)
            return "jdbc:oracle:thin:@//%s:%s/%s" % (self.server, self.port, self.dbservice)
    
    def getDefaultDriver(self):
        return "oracle.jdbc.OracleDriver"

class DB2Connection( JdbcConnection ):
    def getUrl(self):
        portStr = ""
        if self.port != 0:
            portStr = ":" + self.port
        return "jdbc:db2://%s%s/%s" % (self.server, portStr, self.dbname)

    def getDefaultDriver(self):
        return "com.ibm.db2.jcc.DB2Driver"

class PostgresConnection( JdbcConnection ):
    def getUrl(self):
        return "jdbc:postgresql://%s/%s" % (self.server, self.dbname)

    def getDefaultDriver(self):
        return "org.postgresql.Driver"

class SQLServerConnection( JdbcConnection ):
    def getUrl(self):
        databaseurl = self.dburl
        if databaseurl.strip():
            log.detail("Database URL is not empty.")
            return databaseurl
        else:
            portStr = ""
            if self.port != 0:
                portStr = ":" + self.port
            return "jdbc:sqlserver://%s%s;DatabaseName=%s;SelectMethod=cursor;" % ( self.server, portStr, self.dbname)
    
    def getDefaultDriver(self):
        return "com.microsoft.sqlserver.jdbc.SQLServerDriver"


def openDbConnection(dbtype, dbname, dbservice, user, password, server, dburl, port=0, driver=None):
    """Creates new JdbcConnection, opens it, and returns the object.
    Call conn.close() when done.
    """
    if dbtype == 'oracle':
        conn = OracleConnection(dbname, user, password, server, dburl, port,  driver, dbservice)
    elif dbtype == 'postgres':
        conn = PostgresConnection(dbname, user, password, server, dburl,port, driver)
    elif dbtype == 'sqlserver':
        conn = SQLServerConnection(dbname, user, password, server,dburl, port, driver)
    elif dbtype == 'db2':
        conn = DB2Connection(dbname, user, password, server, dburl,port, driver)
    else:
        raise InvalidDatabaseTypeError, "Invalid database type. Type '%s' is not defined." % dbtype

    conn.dbtype  = dbtype

    conn.open()
    return conn


# ---------------------- utils ----------------------

class DbError( Exception ):
    def __init__( self, orig, details ):
        self.orig = orig
        self.details = details
        Exception.__init__( self, str(orig) + "\n  " + details )

    def __str__(self):
        return str(self.orig) + "\n  " + self.details

class InvalidDatabaseTypeError( Exception ):
    def __init__( self, msg ):
        self.msg = msg
        Exception.__init__( self, msg )
    def __str__(self):
        return self.msg

class AbstractMethodInvokedError( Exception ):
    def __init__( self, msg ):
        self.msg = "Invalid usage: Subclass must overwrite %s"%msg
        Exception.__init__( self, self.msg )
    def __str__(self):
        return self.msg

# def cleanDbError(why):
#     """Pretty print common two-line db error."""
#     lines = str(why).split("\n")
#     if len(lines) == 2 and len(lines[1]) < 22:
#         return " ".join(lines)
#     else:
#         return str(why)


# ---------------------- test ----------------------

def _cmdline(args):
    usage = "Usage: %s [-t db-type] [-s server] [-p port] [-d database] [-u user] [-w passwd] [-l logdir] -f file.sql" \
            % os.path.basename( args[0] )
    try:
        ( opts, args ) = getopt.getopt( args[1:], 't:s:p:d:u:w:f:l:')
    except getopt.GetoptError, why:
        print "Error while parsing command line " + why
        sys.exit( usage + " " + str( why ) )
    optmap = {}
    for option, value in opts:
        optmap[option] = value

    logdir = optmap.get("-l", "")
    if logdir:
        log.init(logdir)

    filename = optmap["-f"]
    try:
        conn = openDbConnection(dbtype   = optmap["-t"],
                                dbname   = optmap["-d"],
                                user     = optmap["-u"],
                                password = optmap["-w"],
                                server   = optmap["-s"],
								dburl	 = optmap["-l"],
                                port     = optmap.get("-p", 0))
        executeSqlFile(conn, filename)
        conn.close()
    except (IOError, os.error):
        log.exception()

if __name__ == "__main__":
    _cmdline( sys.argv )

