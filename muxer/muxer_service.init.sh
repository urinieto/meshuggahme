#!/bin/bash

ACTION=$1

REPO_ROOT=$(git rev-parse --show-toplevel)

cd $REPO_ROOT/muxer

if [ -e meshuggahme.default ]; then
    source meshuggahme.default
else
    export MESHUGGAHME_AVCONV_PATH=/usr/bin/avconv
    export MESHUGGAHME_YTDL_PATH=/home/phaedrus/repos/meshuggahme/muxer/youtube-dl
    export MUSHUGGAHME_DL_PATH=/home/phaedrus/tmp/meshuggahme/dl
    export MUSHUGGAHME_OUTPUT_PATH=/home/phaedrus/tmp/meshuggahme/out
    export MUSHUGGAHME_OUTPUT_URL=http://localhost/video
fi

if [ "$MESHUGGAHME_VENV" ]; then
    source $MESHUGGAHME_VENV/bin/activate
fi

function meshuggahme_start() {
    if [ "$MESHUGGAHME_USE_GUNICORN" ]; then
        $MESHUGGAHME_VENV/bin/gunicorn -D -b 127.0.0.1:5000 -w 4 meshuggahme_muxer:app
    else
        python meshuggahme_muxer.py 
    fi
}

function meshuggahme_stop() {
    if [ "$MESHUGGAHME_PIDFILE" ]; then
        kill $(cat $MESHUGGAHME_PIDFILE)
    fi
}

case "$ACTION" in
    start)
        meshuggahme_start
        ;;
    stop)
        meshuggahme_stop
        ;;
    restart)
        meshuggahme_stop
        meshuggahme_start
        ;;
    *)
        echo "It's an init script.  Specify start/stop/restart."
        exit 1
        ;;
esac
