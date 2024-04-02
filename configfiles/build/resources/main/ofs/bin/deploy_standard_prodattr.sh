#! /bin/bash

echo "Deploying standard product attributes definition"
OFS_HOME_CONF_VAR=/usr/local/ofs/conf
OFS_HOME_BIN_VAR=/usr/local/ofs/bin
PROD_ATTRS_INPUT_FILE_NAME=$1
if [ -e "$OFS_HOME_CONF_VAR/$PROD_ATTRS_INPUT_FILE_NAME" ]; then
	echo "Invoking createprodattrdefn cmd"
	$OFS_HOME_BIN_VAR/createprodattrdefn.sh -fileName "$OFS_HOME_CONF_VAR/$PROD_ATTRS_INPUT_FILE_NAME"
fi
