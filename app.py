import os

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def show_files():
    zips = []
    for f in [os.path.join(dp, f) for dp, dn, fn in os.walk('/var/www/aosiprom.com/beta') for f in fn]:
        if f.split('.')[-1] == 'zip':
            zip = f.split('/')[-1]
            zips.append(zip)
    zips.sort()
    return render_template('latest.html', zips=zips)


if __name__ == '__main__':
    app.run()
