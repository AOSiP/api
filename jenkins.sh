PATH="$HOME/bin:$HOME/.local/bin:$PATH"
[[ -n $(pidof flask) ]] && killall flask
[[ -n $(pidof python3) ]] && killall python3
[[ -d "venv" ]] || python3 -m venv ./venv
source venv/bin/activate
./app.py
