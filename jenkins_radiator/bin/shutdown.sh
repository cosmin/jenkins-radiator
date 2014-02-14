#!/bin/bash

if [ ! -f $RADIATOR_HOME/jenkins-radiator.pid ]; then
   echo Do not see a jenkins-radiator.pid file, unable to reliably determine which process to stop.
   exit 1
fi

PID=`cat $RADIATOR_HOME/jenkins-radiator.pid`
if [ -n "$PID" ]; then
   echo Killing Jenkins at PID $PID
   kill $PID
   for i in {0..5}
   do
      if ps $PID >/dev/null 2>&1 ; then
         echo Process killed successfully.
         rm $RADIATOR_HOME/jenkins-radiator.pid
         exit 0
      fi
      sleep 5
   done
fi

echo "Process didn't die nicely, force killing it!"
kill -9 $PID
rm $RADIATOR_HOME/jenkins-radiator.pid