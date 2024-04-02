SCRIPT_DIR=/usr/local/ofs/conf
export SCRIPT_DIR

if [ "$1" = "" ]
then
   echo "Usage: encryptstring.sh <string to encrypt>"
   exit 1
fi

source /usr/local/ofs/bin/set_classpath.sh

/opt/java/openjdk/bin/java com.oatsystems.util.EncryptString $@

