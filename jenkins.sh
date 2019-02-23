PATH="$HOME/bin:$HOME/.local/bin:$PATH"
killall flask
BUILD_ID=Flask FLASK_APP=app.py flask run &
