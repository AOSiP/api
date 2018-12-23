from glob import iglob

from flask import Flask, render_template

app = Flask(__name__)

DIR = '/var/www/aosiprom.com/beta'

@app.route('/')
def show_files():
    zips = []
    for d in iglob(DIR):
        f = iglob(d).sort()[-1]
        if f.split('.')[-1] == 'zip':
            zip = f.split('/')[-1]
            zips.append(zip)
    zips.sort()
    return render_template('latest.html', zips=zips)


if __name__ == '__main__':
    app.run()
