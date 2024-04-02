SCRIPT_DIR=/usr/local/ofs/conf
export SCRIPT_DIR

source /usr/local/ofs/bin/set_classpath.sh

#PATH=$PATH:/opt/mssql-tools/bin
#export PATH
#echo $PATH

/opt/java/openjdk/bin/java  com.oatsystems.fileimport.handler.product.RapidProductUploader $@

