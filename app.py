import os

from flask import Flask, render_template

app = Flask(__name__)

DIR = os.getenv('DIR', '/var/www/aosiprom.com/beta')


def get_date_from_zip(zip):
    return zip.split('-')[-1].split('.')[0]

def get_zips(dir):
    zips = {}
    for f in [os.path.join(dp, f) for dp, dn, fn in os.walk(dir) for f in fn]:
        if f.split('.')[-1] != 'zip':
            continue
        zip = f.split('/')[-1]
        device = zip.split('-')[3]
        if device in zips:
            if get_date_from_zip(zips[device]) > get_date_from_zip(zip):
                continue
        zips[device] = zip
    data = list(zips.values())
    data.sort()
    return data

@app.route('/')
def show_files():
    return render_template('latest.html', zips=get_zips(DIR))

@app.route('/<device>')
def latest_device(device):
    if os.path.isdir(os.path.join(DIR, device)):
        return render_template('device.html', zip=get_zips(os.path.join(DIR, device)), device=device)
    else:
        return "There isn't any build for {} available!".format(device)


if __name__ == '__main__':
    app.run()
