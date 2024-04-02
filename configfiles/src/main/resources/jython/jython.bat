@echo off
@REM $Id: jython.bat,v 1.28 2015/05/26 18:07:30 wlam Exp $
@REM
@REM This file starts the jython interpreter. 
@REM

SET CUR_DIR=%cd%
cd /d "%~dp0..\.."

SET OAT_HOME=%cd%

cd /d "%CUR_DIR%"
SETLOCAL ENABLEDELAYEDEXPANSION
SET LIB_DIR=%OAT_HOME%\ofs\lib
SET OFS_HOME=$USER_INPUT_OFS_ROOT$\ofs

IF NOT EXIST  %OFS_HOME%\ofs\conf (
SET OFS_HOME=%OAT_HOME%\ofs
)

SET LIB_DIR=%OFS_HOME%\ofs\lib

SET OAT_JAVA_CMD=%OAT_HOME%\jdk1.8.0\bin\java.exe

IF NOT EXIST %OAT_JAVA_CMD% (
  SET OAT_JAVA_CMD=%OAT_HOME%\jdk1.7.0\bin\java.exe
)
IF NOT EXIST %OAT_JAVA_CMD% (
  SET OAT_JAVA_CMD=%OAT_HOME%\jdk1.6.0\bin\java.exe
)
IF NOT EXIST %OAT_JAVA_CMD% (
  SET OAT_JAVA_CMD=%OAT_HOME%\jdk1.5.0\bin\java.exe
)
IF NOT EXIST %OAT_JAVA_CMD% (
  SET OAT_JAVA_CMD=%JAVA_HOME%\bin\java.exe
)
IF NOT EXIST %OAT_JAVA_CMD% (
  SET OAT_JAVA_CMD=java.exe
)
SET JYTHON_HOME=%OAT_HOME%\jython

@REM
@REM Note that variables inclosed in 2 dollar signs
@REM are substituted during installation by IA installer.
@REM

set ARGS=
:loop
if [%1] == [] goto end
        set ARGS=%ARGS% %1
        shift
        goto loop
:end

SET JY_CP=%JYTHON_HOME%\jython.jar;%OFS_HOME%\conf;%OFS_HOME%\classes;%OFS_HOME%\lib\*

set CLASSPATH=%JY_CP%

"%OAT_JAVA_CMD%" "-Dedge.home=%OFS_HOME%" "-Dpython.home=%JYTHON_HOME%" org.python.util.jython %ARGS%

