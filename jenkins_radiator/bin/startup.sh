#!/bin/bash

if [ "$(id -u)" == "0" ]; then
   echo "DON'T RUN JENKINS-RADIATOR AS ROOT!"
   echo "(aborting startup.sh)"
   exit 1
fi

if [ "$RADIATOR_HOME" == "" ]; then
   echo '$RADIATOR_HOME not set, aborting.'
   exit 3
fi

if [ -f $RADIATOR_HOME/jenkins-radiator.pid ]; then
   PID=`cat $RADIATOR_HOME/jenkins-radiator.pid`
   if [ -n "$PID" ]; then
      if ps $PID >/dev/null 2>&1 ; then
        echo Jenkins-Radiator already running on PID $PID, not starting.
        exit 4
      fi
   fi
   echo "Stale jenkins-radiator.pid file found ($PID)"
fi


cd $RADIATOR_HOME
nice -n +1 python26 ./manage.py runfcgi method=prefork host=0.0.0.0 port=8803 pidfile=$RADIATOR_HOME/jenkins-radiator.pid

echo "Started Jenkins-Radiator with PID $(cat $RADIATOR_HOME/jenkins-radiator.pid)"