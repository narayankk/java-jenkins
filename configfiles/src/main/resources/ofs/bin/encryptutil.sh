SCRIPT_DIR=/usr/local/ofs/conf
export SCRIPT_DIR

if [ "$1" = "" ]
then
   echo "Usage: encryptutil.sh -e <string to encrypt>"
   echo "Usage: encryptutil.sh -d <string to decrypt>"
   exit 1
fi

source /usr/local/ofs/bin/set_classpath.sh

/opt/java/openjdk/bin/java  org.autoidcenter.util.EncryptionUtilities  $@
