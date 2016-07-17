#!/usr/bin/env python
import sys
from syslog import syslog
from unipath import Path, DIRS_NO_LINKS
import logging
import re

### Settings ###
# Target directories
MOVIE_DIR  = Path('Movies/')
SERIES_DIR = Path('TV Shows/')
MUSIC_DIR  = Path('Music/')
KEEP_ORIGINAL = True # Set false to remove from download directory
AUDIO_FILES = ('wav', 'mp3', 'flac', 'ogg', 'm4a')
VIDEO_FILES = ('mkv', 'avi', 'mp4',)

# Set up logging
logging.basicConfig(filename='/tmp/filesort.log', level=logging.DEBUG)

def sort_movie(torrent_id, torrent_name, save_path):
    pass

def sort_serie(torrent_id, torrent_name, save_path):
    pass

def sort_music(torrent_id, torrent_name, save_path):
    pass

torrent_id = sys.argv[1]
torrent_name = sys.argv[2]
save_path = sys.argv[3]

logging.info('Processing torrent {}: {} in {}'.format(torrent_id, torrent_name,
    save_path))

# Get the name of the title
torrent_path = Path(save_path, torrent_name)
if torrent_path.isdir():
    raw_name = torrent_name
else:
    raw_name = torrent_path.stem

movie_re = None
serie_re = re.compile('([\w.]+)(?=(S\d\dE\d\d))(\2)*')
music_re = None

# Test if this is a TV series
series_match = serie_re.match(raw_name)
if series_match:
    series_name = series_match.group(1).replace('.', ' ').strip()
    episode = series_match.group(2)
    logging.info('Torrent is TV series: {}, episode {}'.format(series_name,
        episode))
