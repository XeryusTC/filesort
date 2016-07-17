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

def remove_samples(file_list):
    return [f for f in file_list if 'sample' not in f.lower()]

def copy_file(src, dst):
    i = 1
    orig = dst
    while dst.exists():
        dst = Path(orig.parent, orig.stem + '-' + str(i) + orig.ext)
        i += 1
        logging.debug('New destination file: {}'.format(dst))
    src.copy(dst)

def sort_episode(series_name, episode, torrent_path):
    # Ensure the series directory exists
    series_dir = Path(SERIES_DIR, series_name)
    series_dir.mkdir(True)

    if torrent_path.isdir():
        files = [torrent_path.listdir('*.' + ext) for ext in VIDEO_FILES]
        files = [f for sublist in files for f in sublist]
        files = remove_samples(files)
        logging.debug('List of files: {}'.format(files))

        if len(files) == 0:
            logging.critical('No video file found in series directory!')
            sys.exit(1)
        elif len(files) == 1:
            dest_file = Path(series_dir,
                series_name + ' - ' + episode + files[0].ext)
            logging.info('Copying single file to destination: {}'.format(
                dest_file))
            copy_file(files[0], dest_file)
        else:
            # There are multiple video files in the directory
            logging.warning('Copying multiple single episode files not' +
                'implemented yet')
            sys.exit(0)
    else:
        if torrent_path.ext not in VIDEO_FILES:
            logging.warning('Unknown video file extention: {}'.format(
                torrent_path.ext))

        dest_file = Path(series_dir, series_name, ' - ', episode,
            torrent_path.ext)

        logging.info('Copying single file to destination: {}'.format(
            dest_file))
        copy_file(torrent_path, dest)

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
    sort_episode(series_name, episode, torrent_path)
