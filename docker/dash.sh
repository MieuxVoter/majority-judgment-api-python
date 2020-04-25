pip install dash dash_daq dash-bootstrap-components
echo "FOOO"
ls /code/*
echo .env.local
pushd dashboard
	python dash_app.py
popd
