from flask import Flask, render_template

import os

app = Flask(__name__)

@app.route('/')
def show_files():
    data = []
    for f in [os.path.join(dp, f) for dp, dn, fn in os.walk('/var/www/aosiprom.com/beta') for f in fn]:
        if f.split('.')[-1] == 'zip':
            n = f.split('/')
            data.append(n[-2]+'/'+n[-1])
    data.sort()
    return render_template('latest.html', data=data)


if __name__ == '__main__':
    app.run()
