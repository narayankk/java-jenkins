#!/bin/bash

OFS_HOME=/usr/local/ofs
OFS_CONF=${OFS_HOME}/conf
RDBMS_CONFIGURATION=${OFS_CONF}/rdbms_config.properties
CONFIGURE_PROPERTIES=${OFS_HOME}/configure.properties

if [ -f "${OFS_CONF}/shared/rdbms_config.properties" ]
then
        echo "Shared RDBMS Configuration Exists & same will be used to prepare configure.properties"
        RDBMS_CONFIGURATION=${OFS_CONF}/shared/rdbms_config.properties
elif [ -f "${OFS_CONF}/shared/rdbms_config.properties" ]
then
        echo "Conf RDBMS Configuration Exists & same will be used to prepare configure.properties"
fi

echo "RDBMS Configuration: ${RDBMS_CONFIGURATION} "
cp ${OFS_HOME}/configure.properties.template ${CONFIGURE_PROPERTIES}

echo "DB_NAME=`cat ${RDBMS_CONFIGURATION} | grep 'senseware.database.name' | cut -d'=' -f 2 `"  >> ${CONFIGURE_PROPERTIES}
echo "DB_HOST=`cat ${RDBMS_CONFIGURATION} | grep 'senseware.database.url' | cut -d'=' -f 2 `"  >> ${CONFIGURE_PROPERTIES}
echo "SQLSERVER_DB_PASSWORD=`cat ${RDBMS_CONFIGURATION} | grep 'senseware.database.password=' | cut -d'=' -f 2 `"  >> ${CONFIGURE_PROPERTIES}
echo "DB_PASSWORD_ENCRYPTED=`cat ${RDBMS_CONFIGURATION} | grep 'senseware.database.password.encrypted' | cut -d'=' -f 2 `"  >> ${CONFIGURE_PROPERTIES}
echo "SQLSERVER_DB_USER=`cat ${RDBMS_CONFIGURATION} | grep 'senseware.database.user' | cut -d'=' -f 2 `"  >> ${CONFIGURE_PROPERTIES}
echo "DB_URL=`cat ${RDBMS_CONFIGURATION} | grep 'senseware.database.connect_string' | sed 's/senseware.database.connect_string=//' `"  >> ${CONFIGURE_PROPERTIES}
echo "SSL_HOST_NAME=localhost"  >> ${CONFIGURE_PROPERTIES}
cd ${OFS_HOME}
sed -i -e 's/\r$//' ${CONFIGURE_PROPERTIES}
echo "Completed Preparation of configure.properties"
