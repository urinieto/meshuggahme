#!/usr/bin/env python

import os

os.environ['MESHUGGAHME_AVCONV_PATH'] = '/usr/bin/avconv'
os.environ['MESHUGGAHME_YTDL_PATH'] = '/home/phaedrus/repos/meshuggahme/muxer/youtube-dl'
os.environ['MESHUGGAHME_DL_PATH'] = '/home/phaedrus/tmp/meshuggahme/dl'
os.environ['MESHUGGAHME_OUTPUT_PATH'] = '/home/phaedrus/tmp/meshuggahme/out'

from muxer import Muxer

gojira = 'https://www.youtube.com/watch?v=BGHlZwMYO9g'
#spears = 'https://www.youtube.com/watch?v=LOZuxwVk7TU'
spears = 'https://youtu.be/LOZuxwVk7TU'

if __name__ == '__main__':
    gojira_muxer = Muxer(yt_url=gojira)
    spears_muxer = Muxer(yt_url=spears)

    gojira_muxer.download_video()
    spears_muxer.download_video()

    gojira_muxer.demux()
    spears_muxer.demux()

    spears_muxer.remux(gojira_muxer.get_audio_file())


