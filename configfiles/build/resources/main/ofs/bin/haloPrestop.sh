SCRIPT_DIR=/usr/local/ofs/conf
export SCRIPT_DIR

source /usr/local/ofs/bin/set_classpath.sh

/opt/java/openjdk/bin/java com.oatsystems.monitoringagent.service.serverstatus.ServerStatusNotifier shutdown