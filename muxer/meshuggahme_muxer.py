#!/usr/bin/env python

import os
import json
from flask import Flask, request, abort
from muxer import Muxer, get_ytid_from_url
from analyzer.meshuggahme import load_models, meshuggahme, improve_normal
from greenlet import greenlet
from Queue import Queue

app_name = 'meshuggahme_muxer'
app = Flask(app_name)

video_url_prefix = os.environ.get('MESHUGGAHME_OUTPUT_URL', 'http://localhost:5000/video')

pidfile = os.environ.get('MESHUGGAHME_PIDFILE', None)
if pidfile and os.path.exists(os.path.dirname(pidfile)):
    with open(pidfile, 'w') as f:
        f.write(os.getpid())

model_dir = os.environ.get('MESHUGGAHME_MODEL_DIR','../notes')
onset_dicts, X, Y, Z = load_models(model_dir)

onset_dir = os.environ.get('MESHUGGAHME_ONSET_DIR','../onsets')

output_dir = os.environ['MESHUGGAHME_OUTPUT_PATH']

muxer_queue = Queue()
muxer_workers = []

def greenlet_muxer_worker():
    global muxer_queue
    global onset_dicts, onset_dir, X, Y, Z

    while True:
        try:
            yt_url = muxer_queue.get()
            m = Muxer(yt_url=yt_url)
            m.download_video()
            m.demux()
            m.convert_to_wav()
            # XXX: Call meshuggahfier here, and use its output in place of m.get_audio_file() 
            meshuggahfied_file = '{output_path}/{ytid}mm.wav'.format(
                output_path=m.output_dir, ytid=m.ytid
            )
            meshuggahme(
                m.get_audio_file(), 
                X, improve_func=improve_normal,
                onset_dicts=onset_dicts, onset_dir=onset_dir,
                metric='correlation', output_file=meshuggahfied_file,
                original_w=6.5
            )
            meshuggahfied_file = m.compress_wav(meshuggahfied_file)
            m.remux(meshugahfied_file).split('/')[-1]
            with open(
                '{output_dir}/{ytid}.status.json'.format(output_dir=output_dir, ytid=m.ytid), 'w'
            ) as f:
                f.write('{"status": "complete"}')
        except Exception as e:
            print repr(e)

for i in range(1,5):
    muxer_workers.append(greenlet(greenlet_muxer_worker))

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
    muxer_queue.put(yt_url)
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
