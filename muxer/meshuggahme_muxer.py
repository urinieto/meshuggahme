#!/usr/bin/env python

import os
import json
import redis
from flask import Flask, request, abort
from muxer import Muxer, get_ytid_from_url
from analyzer.meshuggahme import load_models, meshuggahme, improve_normal

app_name = 'meshuggahme_muxer'
app = Flask(app_name)

video_url_prefix = os.environ.get('MESHUGGAHME_OUTPUT_URL', 'http://localhost:5000/video')

pidfile = os.environ.get('MESHUGGAHME_PIDFILE', None)
if pidfile and os.path.exists(os.path.dirname(pidfile)):
    with open(pidfile, 'w') as f:
        f.write(os.getpid())

output_dir = os.environ['MESHUGGAHME_OUTPUT_PATH']

redis = redis.StrictRedis(host='localhost', port=6379, db=0)

@app.route('/')
def app_version():
    return json.dumps({'app_name': app_name, 'version': 'DUCT_TAPED_DEMO'})

@app.errorhandler(400)
def bad_request():
    return json.dumps({'error': 'Bad Request', 'video_url': None})

@app.route('/status/<ytid>', methods=['GET'])
def mux_demux_status(ytid):
    try:
        with open(
            '{output_dir}/{ytid}.status.json', 'r'.format(output_dir=output_dir, ytid=ytid)
        ) as f:
            json = f.read()
        return json
    except IOError:
        abort(400)

@app.route('/mux_demux', methods=['GET', 'POST'])
def mux_demux():
    yt_url = request.args.get('yt_url', None)
    if yt_url is None:
        abort(400)
    ytid = get_ytid_from_url(yt_url)
    redis.rpush('yturls', yt_url)
    with open(
        '{output_dir}/{ytid}.status.json'.format(output_dir=output_dir, ytid=ytid), 'w'
    ) as f:
        f.write('{"status": "processing"}')
    return json.dumps(
        {
            'video_url': '{video_url_prefix}/{ytid}.mp4'.format(
                video_url_prefix=video_url_prefix, ytid=ytid
            ),
            'status_file': '{video_url_prefix}/{ytid}.status.json'.format(
                video_url_prefix=video_url_prefix, ytid=ytid
            )
        }
    )

if __name__ == '__main__':
    app.run()
