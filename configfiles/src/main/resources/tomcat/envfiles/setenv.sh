#! /bin/sh
# set the classpath
export CLASSPATH="$CATALINA_HOME/../ofs/conf/"

# Check for application specific parameters at startup
if [ -r "$CATALINA_BASE/bin/appenv.sh" ]; then
  . "$CATALINA_BASE/bin/appenv.sh"
fi
