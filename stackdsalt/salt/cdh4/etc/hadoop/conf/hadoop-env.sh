# Set Hadoop-specific environment variables here.

# The only required environment variable is JAVA_HOME.  All others are
# optional.  When running a distributed configuration it is best to
# set JAVA_HOME in this file, so that it is correctly defined on
# remote nodes.

# Set JAVA_HOME
export JAVA_HOME="{{ pillar.jdk6.java_home }}"

# Configure SSH options
export HADOOP_SSH_OPTS="-o StrictHostKeyChecking=no"

# Configure Hadoop logging location
#export HADOOP_LOG_DIR=/var/log/hadoop

# Pid files go here
#export HADOOP_PID_DIR=/var/run/hadoop
