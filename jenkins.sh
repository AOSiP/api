PATH="$HOME/bin:$HOME/.local/bin:$PATH"
killall flask
FLASK_APP=app.py flask run &
