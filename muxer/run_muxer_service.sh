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

python meshuggahme_muxer.py 
