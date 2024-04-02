SCRIPT_DIR=/usr/local/ofs/conf
export SCRIPT_DIR

source /usr/local/ofs/bin/set_classpath.sh

${SCRIPT_DIR}/haloserver status $@ | grep "Service Manager: Running" >/dev/null 2>&1
if [ $? -eq 0 ] ; then
   /opt/java/openjdk/bin/java com.oatsystems.service.ws.axis.locationexport.LocationExportCommandExecutor $@
else
   echo "The OAT Edge Server is not running.  The OAT Edge Server must be running in order to run this script."
fi
