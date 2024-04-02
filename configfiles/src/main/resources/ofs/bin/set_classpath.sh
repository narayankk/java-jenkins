# **************************************************
# ** Loop the lib directory and add the classpath.**
# **************************************************
OAT_HOME=/usr/local
CLASSPATH=$CLASSPATH:$OAT_HOME/ofs/conf/shared:$OAT_HOME/ofs/conf:$OAT_HOME/tomcat/webapps/axis/WEB-INF/classes:$OAT_HOME/tomcat/webapps/axis/WEB-INF/lib/*

for f in `find $OAT_HOME/tomcat/webapps/axis/WEB-INF/lib -maxdepth 1 -type f -name "*.zip"`
do
  CLASSPATH=$CLASSPATH:$f
done

#echo $CLASSPATH

export CLASSPATH