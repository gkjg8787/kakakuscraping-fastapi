psret=`ps aux | grep fastapi | grep -v grep | awk '{print $2}'`

echo "kill " $psret

kill -9 $psret

