#!/bin/bash

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

REPO_ROOT=$(git rev-parse --show-toplevel)

cd $REPO_ROOT/muxer

if [ "$MESHUGGAHME_USE_GUNICORN" ]; then
    $MESHUGGAHME_VENV/bin/gunicorn -D -b 127.0.0.1:5000 -w 4 meshuggahme_muxer:app
else
    python meshuggahme_muxer.py 
fi
