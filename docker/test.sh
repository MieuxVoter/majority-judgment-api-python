tmpfile=$(mktemp /tmp/mj-api.XXXX)
echo "SECRET=mysecrettoken" >> $tmpfile
echo "SQLITE=True" >> $tmpfile

docker run --env-file $tmpfile  \
	majority-judgment/api-python:latest \
	-c "pip install -r requirements-dev.txt; pytest"
