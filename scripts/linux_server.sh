cd ..
. .env/bin/activate
export FLASK_APP="webserver"
export FLASK_ENV="development"
export FLASK_DEBUG="1"
# chromium-browser 127.0.0.1:5000 &
python -m flask run --with-threads