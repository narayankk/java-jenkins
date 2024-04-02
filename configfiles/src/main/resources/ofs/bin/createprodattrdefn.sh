#! /bin/bash

OPTION="createView"
UPGRADEOPTION=""
ASSETTYPE=""

if [ "$2" = -isAssetType ] || [ "$1" = -isAssetType ]
then
   echo "Usage: createprodattrdefn.sh [-noView] -fileName <path to file with asset definitions> [-isAssetType]"
   echo "  -noView specify if view creation is not needed; by default view is created"
   echo "  -isAssetType specify if asset definition will be uploaded; by default it is assumed that"
   echo "   product attribute definition will be uploaded."
   exit 1
fi

if [ "$4" = -isAssetType ]
then
 ASSETTYPE=assetType
fi

if [ "$5" = -isAssetType ]
then
 ASSETTYPE=assetType
 shift
    if [ X"$6" = X"" ]
    then
 	   echo "Usage: createprodattrdefn.sh [-noView] -fileName <path to file with asset definitions> [-isAssetType]"
 	   echo "  -noView specify if view creation is not needed; by default view is created"
 	   echo "  -isAssetType specify if asset definition will be uploaded; by default it is assumed that"
 	   echo "   product attribute definition will be uploaded."
 	   exit 1
   fi
fi

if [ "$3" = -isAssetType ] && [ "$2" != -fileName ]
then
 ASSETTYPE=assetType
elif [ "$3" = -isAssetType ] && [ "$2" = -fileName ]
then
   echo "Usage: createprodattrdefn.sh [-noView] -fileName <path to file with asset definitions> [-isAssetType]"
   echo "  -noView specify if view creation is not needed; by default view is created"
   echo "  -isAssetType specify if asset definition will be uploaded; by default it is assumed that"
   echo "   product attribute definition will be uploaded."
   exit 1
fi

if [ "$2" = -upgrade ] || [ "$1" = -upgrade ]
then
   echo "Usage: createprodattrdefn.sh [-noView] -fileName <path to file with asset definitions> [-isAssetType]"
   echo "  -noView specify if view creation is not needed; by default view is created"
   echo "  -isAssetType specify if asset definition will be uploaded; by default it is assumed that"
   echo "   product attribute definition will be uploaded."
   exit 1
fi

if [ "$5" = -upgrade ]
then
 UPGRADEOPTION=upgrade
  shift
     if [ X"$6" = X"" ]
     then
  	   echo "Usage: createprodattrdefn.sh [-noView] -fileName <path to file with asset definitions> [-isAssetType]"
  	   echo "  -noView specify if view creation is not needed; by default view is created"
  	   echo "  -isAssetType specify if asset definition will be uploaded; by default it is assumed that"
  	   echo "   product attribute definition will be uploaded."
  	   exit 1
   fi
fi

if [ "$4" = -upgrade ]
then
 UPGRADEOPTION=upgrade
fi

if [ "$3" = -upgrade ] && [ "$2" != -fileName ]
then
 UPGRADEOPTION=upgrade
elif [ "$3" = -upgrade ] && [ "$2" = -fileName ]
then 
   echo "Usage: createprodattrdefn.sh [-noView] -fileName <path to file with asset definitions> [-isAssetType]"
   echo "  -noView specify if view creation is not needed; by default view is created"
   echo "  -isAssetType specify if asset definition will be uploaded; by default it is assumed that"
   echo "   product attribute definition will be uploaded."
   exit 1
fi

if [ "$1" = -noView ]
then
  OPTION="noView"
  shift
fi

if [ $1 = -fileName ]
then
   shift
   if [ X"$1" = X"" ]
   then
	   echo "Usage: createprodattrdefn.sh [-noView] -fileName <path to file with asset definitions> [-isAssetType]"
	   echo "  -noView specify if view creation is not needed; by default view is created"
	   echo "  -isAssetType specify if asset definition will be uploaded; by default it is assumed that"
	   echo "   product attribute definition will be uploaded."
	   exit 1
   fi
else
   echo "Usage: createprodattrdefn.sh [-noView] -fileName <path to file with asset definitions> [-isAssetType]"
   echo "  -noView specify if view creation is not needed; by default view is created"
   echo "  -isAssetType specify if asset definition will be uploaded; by default it is assumed that"
   echo "   product attribute definition will be uploaded."
   exit 1
fi

CUR_DIR=`pwd`
SCRIPT_DIR=/usr/local
#JAVA_HOME=/usr/local/OATxpress/jdk1.8.0
#PATH=/usr/local/OATxpress/jdk1.8.0/bin:${PATH}
LIBS=/usr/local/ofs/lib
BIN=/usr/local/ofs/bin
CONF=/usr/local/ofs/conf
DEFAULT_CONF=/usr/local/ofs/default/conf/metadata
DEFAULT_DM=/usr/local/ofs/default/conf
LOCAL_CONF=/usr/local/ofs/local/conf/metadata
DBTYPE=sqlserver
SERVER_MODE=SITE

if [ "$SERVER_MODE" = "ENMS" ] 
  then
   echo "Not allowed to create product attribute on OAT EPC Number Manager"
   exit 1
fi

if [ "$SERVER_MODE" = "CCS" ] 
  then
   SQL_FOLDER=sql_ent
   CCS_FOLDER=ccs
fi

if [ "$SERVER_MODE" = "SITE" ] 
 then
   SQL_FOLDER=sql_site
   CCS_FOLDER=enterprise
fi

if [ "$SERVER_MODE" = "EDM" ]
 then
   SQL_FOLDER=sql_ent
   CCS_FOLDER=edm
fi

source ${BIN}/set_classpath.sh
CLASSPATH=$CLASSPATH:${LIBS}/javax.el-api-2.2.5.jar
export CLASSPATH

ATTRMERGEFILE=product-metadata.xml.in.m

${SCRIPT_DIR}/ofs/conf/haloserver dbstatus | grep "Database is running OK" >/dev/null 2>&1

if [ $? -eq 0 ] 
 then
   java com.oatsystems.uddme.tools.GenerateProdAttrMetaData $1 $OPTION $UPGRADEOPTION $ASSETTYPE

   if [ $? -eq 0 ] 
    then
      if [ -f ${ATTRMERGEFILE}  ] 
      then    
        echo Copying ${DEFAULT_CONF}/product-metadata.xml to ${CONF}/metadata/product-metadata.xml
	cp  ${DEFAULT_CONF}/product-metadata.xml ${CONF}/metadata/product-metadata.xml >/dev/null 2>&1

      echo Merging generated $ATTRMERGEFILE into product-metadata.xml
      if [ ! -d ${SCRIPT_DIR}/ofs/local/conf/metadata ] 
      then
		  mkdir -p ${SCRIPT_DIR}/ofs/local/conf/metadata
      fi
      cp $ATTRMERGEFILE ${SCRIPT_DIR}/ofs/local/conf/metadata/ >/dev/null 2>&1

	echo "Merging all product-metadata* files into product-metadata.xml"
	for var in `find ${LOCAL_CONF} -maxdepth 1 -type f -name "product-metadata*.m*"`
	do
	    ${SCRIPT_DIR}/ofs/bin/jython mergeXml.py -i ${CONF}/metadata/product-metadata.xml ${var} ${CONF}/metadata/product-metadata.xml
	done
	
	echo "Merged all product-metadata* files into product-metadata.xml"

      echo Synchronizing metadata with d/b
    fi
     if [ ! -d ${SCRIPT_DIR}/ofs/local/conf ] 
           then
     		  mkdir -p ${SCRIPT_DIR}/ofs/local/conf
      fi
      
     cp ${DEFAULT_DM}/mds-etl-config.xml ${CONF}/mds-etl-config.xml >/dev/null 2>&1
#    cp ${DEFAULT_DM}/mds-etl-no-prod-server-mapping-config.xml ${CONF}/mds-etl-no-prod-server-mapping-config.xml >/dev/null 2>&1
#    cp ${DEFAULT_DM}/mds-etl-edm-no-prod-server-mapping-config.xml ${CONF}/mds-etl-edm-no-prod-server-mapping-config.xml >/dev/null 2>&1
     cp ${DEFAULT_DM}/ccs-edm-dm-spec.xml ${CONF}/ccs-edm-dm-spec.xml >/dev/null 2>&1
     cp ${DEFAULT_DM}/default-ccs-dm-spec.xml ${CONF}/default-ccs-dm-spec.xml >/dev/null 2>&1
     cp ${DEFAULT_DM}/default-ccs-dm-no-product-mapping-spec.xml ${CONF}/default-ccs-dm-no-product-mapping-spec.xml >/dev/null 2>&1
     
     cp ${SCRIPT_DIR}/ofs/bin/mds-etl-config.xml.m ${SCRIPT_DIR}/ofs/local/conf >/dev/null 2>&1
     cp ${SCRIPT_DIR}/ofs/bin/mds-etl-no-prod-server-mapping-config.xml.m ${SCRIPT_DIR}/ofs/local/conf >/dev/null 2>&1
     cp ${SCRIPT_DIR}/ofs/bin/mds-etl-edm-no-prod-server-mapping-config.xml.m ${SCRIPT_DIR}/ofs/local/conf >/dev/null 2>&1
     cp ${SCRIPT_DIR}/ofs/bin/ccs-edm-dm-spec.xml.m ${SCRIPT_DIR}/ofs/local/conf >/dev/null 2>&1
     cp ${SCRIPT_DIR}/ofs/bin/default-ccs-dm-spec.xml.m ${SCRIPT_DIR}/ofs/local/conf >/dev/null 2>&1
     cp ${SCRIPT_DIR}/ofs/bin/default-ccs-dm-no-product-mapping-spec.xml.m ${SCRIPT_DIR}/ofs/local/conf >/dev/null 2>&1
     
      if [ "$OPTION" = "createView" ]
	then
          if [ ! -d ${SCRIPT_DIR}/ofs/local/${SQL_FOLDER}/ALWAYS/${DBTYPE} ] 
	  then
              mkdir -p ${SCRIPT_DIR}/ofs/local/${SQL_FOLDER}/ALWAYS/${DBTYPE}
          fi
	  
	  rm -f ${SCRIPT_DIR}/ofs/local/${SQL_FOLDER}/ALWAYS/${DBTYPE}/prodattrs_view*.sql
          cp ${SCRIPT_DIR}/ofs/bin/productattrs_table_${DBTYPE}.sql ${SCRIPT_DIR}/ofs/local/${SQL_FOLDER}/ALWAYS/${DBTYPE} >/dev/null 2>&1
	  cp ${SCRIPT_DIR}/ofs/bin/productattrs_view_${DBTYPE}.sql ${SCRIPT_DIR}/ofs/local/${SQL_FOLDER}/ALWAYS/${DBTYPE} >/dev/null 2>&1
	  
	  if [ -f ${SCRIPT_DIR}/ofs/bin/upgrade_populate_productattrs_${DBTYPE}.sql ]
	            then
	                cp ${SCRIPT_DIR}/ofs/bin/upgrade_populate_productattrs_${DBTYPE}.sql ${SCRIPT_DIR}/ofs/local/${SQL_FOLDER}/ALWAYS/${DBTYPE} >/dev/null 2>&1
          fi
          
          ${BIN}/deploy -f -l ${SCRIPT_DIR}/ofs/log -r ${SCRIPT_DIR}/ofs/local >/dev/null 2>&1
          if [ ! -d  ${SCRIPT_DIR}/ofs/bin/com/oatsystems/udm/logicalProduct ]
	  then
              mkdir -p ${SCRIPT_DIR}/ofs/bin/com/oatsystems/udm/logicalProduct
          fi
          cp  ${SCRIPT_DIR}/ofs/bin/ProductAttrs.hbm.xml  ${SCRIPT_DIR}/ofs/bin/com/oatsystems/udm/logicalProduct >/dev/null 2>&1
	  
	  cd ${BIN}
          jar uf ${SCRIPT_DIR}/ofs/lib/$CCS_FOLDER/${DBTYPE}_hbm.jar  com
          jar uf ${SCRIPT_DIR}/ofs/lib/site/${DBTYPE}_hbm.jar  com
          if [ ! -d  ${SCRIPT_DIR}/ofs/local/lib/$CCS_FOLDER ] 
	  	  then
	  	      mkdir -p ${SCRIPT_DIR}/ofs/local/lib/$CCS_FOLDER
	  fi
	  cp ${SCRIPT_DIR}/ofs/lib/$CCS_FOLDER/${DBTYPE}_hbm.jar ${SCRIPT_DIR}/ofs/local/lib/$CCS_FOLDER >/dev/null 2>&1
	  if [ ! -d  ${SCRIPT_DIR}/ofs/local/lib/site ] 
	  	  	  then
	  	  	      mkdir -p ${SCRIPT_DIR}/ofs/local/lib/site
	  fi
	  cp ${SCRIPT_DIR}/ofs/lib/site/${DBTYPE}_hbm.jar ${SCRIPT_DIR}/ofs/local/lib/site >/dev/null 2>&1          
	  cd ${CUR_DIR}
	  
	  java com.oatsystems.uddme.tools.GenerateProdAttrMetaData "temp_table"
	  
	  echo Completed Deploy
      fi
     		
   fi
 else 
   echo The Database is not running.  This script requires that the database be started in order to run.
fi