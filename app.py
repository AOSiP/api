import os

from flask import Flask, render_template

app = Flask(__name__)

DIR = os.getenv('DIR', '/var/www/aosiprom.com/beta')


def get_date_from_zip(zip):
    return zip.split('-')[-1].split('.')[0]


@app.route('/')
def show_files():
    zips = {}
    for f in [os.path.join(dp, f) for dp, dn, fn in os.walk(DIR) for f in fn]:
        if f.split('.')[-1] != 'zip':
            continue
        zip = f[-1].split('/')[-1]
        device = zip.split('-')[3]
        if zips[device]:
            if get_date_from_zip(zips[device]) > get_date_from_zip(zip):
                continue
        zips[device] = zip
    data = list(zips.values())
    data.sort()
    return render_template('latest.html', zips=data)


if __name__ == '__main__':
    app.run()
