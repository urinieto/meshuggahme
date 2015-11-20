#!/usr/bin/env python

# Needed config:
#  - Download directory
#  - Output file directory
#  - Path to youtube-dl
#  - Path to avconv

import os
import re
import subprocess
import requests

class MissingYouTubeURL(Exception):
    pass

def get_ytid_from_url(yt_url):
    ytdomain = yt_url.split('/')[2]

    if ytdomain.endswith('youtube.com'):
        # A long time ago, I was a perl programmer...  Sorry.
        return dict([kv.split('=') for kv in yt_url.split('?')[1].split('&')])['v']

    return yt_url.split('/')[3]

class Muxer:
    def __init__(self, yt_url=None):
        self.yt_url = yt_url
        self.ytdl = os.environ['MESHUGGAHME_YTDL_PATH']
        self.avconv = os.environ['MESHUGGAHME_AVCONV_PATH']
        self.download_dir = os.environ['MESHUGGAHME_DL_PATH']
        self.output_dir = os.environ['MESHUGGAHME_OUTPUT_PATH']

        self.dl_file = None
        self.silent_video_out = None
        self.audio_out = None
        self.remux_out = None

    def normalize_yt_url(self, yt_url):
        if yt_url is None: 
            if self.yt_url is None:
                raise MissingYouTubeURL
            yt_url = self.yt_url

        ytdomain = yt_url.split('/')[2]

        if ytdomain.endswith('youtube.com'):
            # A long time ago, I was a perl programmer...  Sorry.
            self.ytid = dict([kv.split('=') for kv in yt_url.split('?')[1].split('&')])['v']
            return yt_url

        self.ytid = yt_url.split('/')[3]
        r = requests.head(yt_url)
        return r.headers['location']

    def download_video(self, yt_url=None):
        yt_url = self.normalize_yt_url(yt_url)

        if not os.path.exists('{download_path}/{ytid}.mp4'.format(
            download_path = self.download_dir,
            ytid = self.ytid
        )):
            #youtube-dl --no-playlist -o {download-path}/%(id)s.%(ext)s {youtube-long-url}
            subprocess.call(
                '{ytdl} --no-playlist -o {download_path}/{ytid}.mp4 {yt_url}'.format(
                    ytdl = self.ytdl,
                    download_path = self.download_dir,
                    ytid = self.ytid,
                    yt_url = yt_url
                ).split(' ')
            )
        # XXX: Eh.  Maybe should check this actually worked?  Meh.  That's for production ready code...
        self.dl_file = '{download_path}/{ytid}.mp4'.format(
            download_path = self.download_dir,
            ytid = self.ytid
        )
        return True

    def demux(self):
        if self.dl_file is None:
            return False

        if not os.path.exists('{output_path}/{ytid}-silent.mp4'.format(
            output_path = self.output_dir,
            ytid = self.ytid
        )):
            #avconv -i {download-path}/%(id)s.%(ext)s -map 0:1 -c copy {output-path}/%(id)s.aac
            subprocess.call(  # Extract video
                '{avconv} -y -i {dl_video} -map 0:0 -c copy {output_path}/{ytid}-silent.mp4'.format(
                    avconv = self.avconv,
                    dl_video = self.dl_file,
                    output_path = self.output_dir,
                    ytid = self.ytid
                ).split(' ')
            )
        if not os.path.exists('{output_path}/{ytid}.aac'.format(
            output_path = self.output_dir,
            ytid = self.ytid
        )):
            subprocess.call(  # Extract audio
                '{avconv} -y -i {dl_video} -map 0:1 -c copy {output_path}/{ytid}.aac'.format(
                    avconv = self.avconv,
                    dl_video = self.dl_file,
                    output_path = self.output_dir,
                    ytid = self.ytid
                ).split(' ')
            )
        # XXX: Eh.  Maybe should check this actually worked?  Meh.  That's for production ready code...
        self.silent_video_out = '{output_path}/{ytid}-silent.mp4'.format(
            output_path = self.output_dir,
            ytid = self.ytid
        )

    def convert_to_wav(self):
        if not os.path.exists('{output_path}/{ytid}.wav'.format(
            output_path = self.output_dir,
            ytid = self.ytid
        )):
            subprocess.call(
                '{avconv} -y -i {output_path}/{ytid}.aac {output_path}/{ytid}.wav'.format(
                    avconv = self.avconv,
                    output_path = self.output_dir,
                    ytid = self.ytid
                ).split(' ')
            )
        self.audio_out = '{output_path}/{ytid}.wav'.format(
            output_path = self.output_dir,
            ytid = self.ytid
        )

    def get_audio_file(self):
        return self.audio_out

    def compress_wav(self, wavfile):
        if not os.path.exists('{output_path}/{ytid}mm.mp3'.format(
            output_path = self.output_dir,
            ytid = self.ytid
        )):
            subprocess.call(
                '{avconv} -y -i {wavfile} {output_path}/{ytid}mm.mp3'.format(
                    avconv = self.avconv,
                    wavfile = wavfile,
                    output_path = self.output_dir,
                    ytid = self.ytid
                ).split(' ')
            )
        return '{output_path}/{ytid}mm.mp3'.format(
            output_path = self.output_dir,
            ytid = self.ytid
        )

    def remux(self, new_audio_track):
        if not os.path.exists('{output_path}/{ytid}.mp4'.format(
            output_path = self.output_dir,
            ytid = self.ytid
        )):
            subprocess.call(
                '{avconv} -y -i {silent_video} -i {new_audio_track} -c copy {output_path}/{ytid}.mp4'.format(
                    avconv = self.avconv,
                    silent_video = self.silent_video_out,
                    new_audio_track = new_audio_track,
                    output_path = self.output_dir,
                    ytid = self.ytid
                ).split(' ')
            )
        self.remux_out = '{output_path}/{ytid}.mp4'.format(
            output_path = self.output_dir,
            ytid = self.ytid
        )
        return self.remux_out

    def get_output_file(self):
        return self.remux_out
