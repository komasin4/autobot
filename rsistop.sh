ps -ef | grep python3 | grep rsitest.py | awk {'print $2'} | xargs kill -9
echo
echo
echo "프로세스 확인..."
echo `ps -ef | grep python3 | grep rsitest.py` 
