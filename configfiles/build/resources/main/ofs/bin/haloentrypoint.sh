#!/bin/bash

echo "###"
echo "### Start of /usr/local/ofs/bin/haloentrypoint.sh"
echo "###"

# Enters the /workspace
cd "/usr/local/ofs/conf";

# TIMEZONE run
if [ -n "$TIMEZONE" ] ; then
   echo "### Enforce TIMEZONE config : $TIMEZONE"
   TZ="$TIMEZONE";
   export TZ;
fi

# LANGUAGE run
if [ -n "$LANGUAGE" ] ; then
   echo "### Enforce LANGUAGE config : $LANGUAGE"
   locale-gen "$LANGUAGE";
fi


targetEnvironment=Engineering

# In this approach, needs to set TARGET_ENVIRONMENT variable either in Docker Command or Docker Compose file or AKS Deployment file.
if [ -n "$TARGET_ENVIRONMENT" ] ; then
    if [ "${TARGET_ENVIRONMENT,,}" == "production" ]; then
        echo "Supplied Environment is Production"
        targetEnvironment=production
    fi
fi

echo "Supplied Environment Variable: $TARGET_ENVIRONMENT"
echo "Target Environment Variable: $targetEnvironment"

# Another Approach: Chain the execution commands. To not loose this alternative, commenting this.
#if [[ -d "/usr/local/ofs/conf/shared" ]]; then
#    FILE=/usr/local/ofs/conf/shared/profile.properties
#    if [[ -f "$FILE" ]]; then
#       echo "$FILE exists."
#       targetEnvironment=`grep -l --null "profile="  $FILE | xargs -0 sed -n '/profile=/s/profile=//p'`
#       echo "Changing Target Environment: $targetEnvironment"
#    fi
#else
#  echo "/usr/local/ofs/conf/shared folder is not existing, hence targetEnvironment is going to be Non-Production : $targetEnvironment "
#fi

if [ "$targetEnvironment" != "production" ]; then
    echo "Not Matches... Target Environment is $targetEnvironment"
    exec "$@"
    #/usr/local/ofs/conf/haloserver start
else
    echo "Matches... Target Environment is $targetEnvironment"
    PROD_DIR="/usr/local/ofs/production_overrides/log4j.properties"
    DST_DIR="/usr/local/ofs/conf"
	cp "$PROD_DIR" "$DST_DIR"
	if [$? -eq 0]; then
		echo "log4j properties overridden by production's log4j"
	else
		echo "log4j properties not overridden by production's log4j"
	fi
    #/opt/java/openjdk/jre/bin/java -Xms3072m -Xmx3072m -Xloggc:/usr/local/ofs/log/memory_usage.log -Djava.util.Arrays.useLegacyMergeSort=true -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/usr/local/ofs/log -Dorg.apache.activemq.default.directory.prefix=/usr/local/ofs/ -server -XX:+ForceTimeHighResolution -Dfile.encoding=UTF-8 -Djavax.net.ssl.keyStore=/usr/local/ofs/conf/ofsclient.jks -Djavax.net.ssl.keyStorePassword=apollo -Djavax.net.ssl.trustStore=/usr/local/ofs/conf/ofsclient.jks -Djavax.net.ssl.trustStorePassword=apollo -XX:MaxPermSize=256m -Djava.security.auth.login.config=/usr/local/ofs/conf/ldap_msad.conf -Dorg.apache.jasper.runtime.BodyContentImpl.LIMIT_BUFFER=true -Djava.awt.headless=true -Djava.security.policy=/usr/local/ofs/conf/server.policy -Dsun.net.client.defaultReadTimeout=15000 -Dsun.net.client.defaultConnectTimeout=15000 -Dcatalina.base=/usr/local/tomcat -Dcatalina.home=/usr/local/tomcat -Dcom.jolbox.bonecp.ignoreSqlCodes=61000 -Djava.io.tmpdir=/usr/local/tomcat/temp -Djava.endorsed.dirs=/usr/local/tomcat/common/endorsed -Dlog4j.defaultInitOverride=true -classpath /usr/local/ofs/conf/shared:/usr/local/ofs/conf:/opt/java/openjdk/lib/tools.jar:/usr/local/tomcat/bin/bootstrap.jar:/usr/local/tomcat/bin/tomcat-juli.jar org.apache.catalina.startup.Bootstrap start
	TOMCAT_START_CMD=`./haloserver printCmd | grep FINALIZED_COMMAND: | sed -r 's/FINALIZED_COMMAND://g' `
	echo "Following Command is Used to Start Tomcat: $TOMCAT_START_CMD "
	$TOMCAT_START_CMD

fi

echo "###"
echo "### Finished /usr/local/ofs/bin/haloentrypoint.sh"
echo "###"
echo "###"
