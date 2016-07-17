#!/usr/bin/env python
import sys
from syslog import syslog
from unipath import Path, DIRS_NO_LINKS
import logging

### Settings ###
# Target directories
MOVIE_DIR  = Path('Movies/')
SERIES_DIR = Path('TV Shows/')
MUSIC_DIR  = Path('Music/')
KEEP_ORIGINAL = True # Set false to remove from download directory

# Set up logging
logging.basicConfig(filename='/tmp/filesort.log', level=logging.DEBUG)
logger = logging.logger(__name__)

def sort_movie(torrent_id, torrent_name, save_path):
    pass

def sort_serie(torrent_id, torrent_name, save_path):
    pass

def sort_music(torrent_id, torrent_name, save_path):
    pass

torrent_id = sys.argv[1]
torrent_name = sys.argv[2]
save_path = sys.argv[3]

logging.info('Processing torrent {}: {} in {}', torrent_id, torrent_name,
    save_path)
