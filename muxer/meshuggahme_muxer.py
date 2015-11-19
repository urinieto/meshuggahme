#!/usr/bin/env python

import os
import json
from flask import Flask, request, abort
from muxer import Muxer

app_name = 'meshuggahme_muxer'
app = Flask(app_name)

video_url_prefix = os.environ.get('MUSHUGGAHME_OUTPUT_URL', 'http://localhost:5000/video')

pidfile = os.environ.get('MESHUGGAHME_PIDFILE', None)
if os.path.exists(os.path.dirname(pidfile)):
    with open(pidfile, 'w') as f:
        f.write(os.getpid())

@app.route('/')
def app_version():
    return json.dumps({'app_name': app_name, 'version': 'DUCT_TAPED_DEMO'})

@app.errorhandler(400)
def bad_request():
    return json.dumps({'error': 'Bad Request', 'video_url': None})

@app.route('/mux_demux', methods=['GET', 'POST'])
def mux_demux():
    yt_url = request.args.get('yt_url', None)
    if yt_url is None:
        abort(400)
    m = Muxer(yt_url=yt_url)
    m.download_video()
    m.demux()
    # XXX: Call meshuggahfier here, and use its output in place of m.get_audio_file() 
    outfile = m.remux(m.get_audio_file()).split('/')[-1]
    return json.dumps(
        {
            'video_url': '{video_url_prefix}/{outfile}'.format(
                video_url_prefix=video_url_prefix, outfile=outfile
            )
        }
    )

if __name__ == '__main__':
    app.run()
