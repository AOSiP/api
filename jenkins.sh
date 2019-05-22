PATH="$HOME/bin:$HOME/.local/bin:$PATH"
[[ -n $(pidof flask) ]] && killall flask
[[ -n $(pidof python3) ]] && killall python3
[[ -d "venv" ]] || python3 -m venv ./venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
echo "Starting up!"
./app.py
