PATH="$HOME/bin:$HOME/.local/bin:$PATH"
[[ -n $(pidof flask) ]] && killall flask
[[ -n $(pidof python3) ]] && killall python3
[[ -d "venv" ]] || python3.8 -m venv ./venv
source venv/bin/activate
python3.8 -m pip install -r requirements.txt
echo "Starting up!"
gunicorn app:app --workers=$(nproc) -b :5000
