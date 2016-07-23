#!/usr/bin/env python
from __future__ import print_function
import sys
from syslog import syslog
from unipath import Path, FILES_NO_LINKS
import logging
import re
import tmdbsimple as tmdb
import datetime

### Settings ###
tmdb.API_KEY = '0ea9d4136175cd4c4ce3ad6d4a7c40fb'
# Target directories
MOVIE_DIR  = Path('Movies/')
SERIES_DIR = Path('TV Shows/')
MUSIC_DIR  = Path('Music/')
KEEP_ORIGINAL = True # Set false to remove from download directory
AUDIO_FILES = ('wav', 'mp3', 'flac', 'ogg', 'm4a')
VIDEO_FILES = ('mkv', 'avi', 'mp4', 'mov', 'mpeg', 'wmv', 'flv', 'm4v')

### Constants ###
ANY_MEDIA = 0
TV_MEDIA  = 1

class MediaNotFoundInTMDBException(Exception):
    pass


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

def find_media(name, media=ANY_MEDIA):
    search = tmdb.Search()
    name = name.replace('.', ' ').strip()
    logging.debug('Searching for "{}"'.format(name))
    if media == ANY_MEDIA:
        search_method = search.multi
    elif media == TV_MEDIA:
        search_method = search.tv
    response = search_method(query=name)

    # When there are results we can just return them
    if search.total_results > 0:
        logging.debug('Found {} results for the query'.format(
            search.total_results))
        return (search, name)

    # Otherwise start removing information, start with the date
    logging.debug('Could not find media, removing dates first')
    name = re.sub(r'\d{4}', '', name).strip()
    response = search_method(query=name)
    if search.total_results > 0:
        logging.debug('Found {} results for the updated query {}'.format(
            search.total_results, name))
        return (search, name)

    raise MediaNotFoundInTMDBException()


def deluge(torrent_id, torrent_name, save_path):
    # Set up logging
    logging.basicConfig(filename='/tmp/filesort.log', level=logging.DEBUG)

    logging.info('Processing torrent from deluge {}: {} in {}'.format(
        torrent_id, torrent_name, save_path))

    # Get the name of the title
    torrent_path = Path(save_path, torrent_name)
    if torrent_path.isdir():
        raw_name = torrent_name
    else:
        raw_name = torrent_path.stem

    # Test if this is a TV series
    serie_re = re.compile(r'([\w.]+)(?=(S\d{2}E\d{2}))(\2)*')
    series_match = serie_re.match(raw_name)
    if series_match:
        series_name = series_match.group(1).replace('.', ' ').strip()
        episode = series_match.group(2)

        # Get information from TMDB about the series
        try:
            search, name = find_media(series_name, TV_MEDIA)

            # Reduce the results from the TMDB search to one final answer
            # Use the newest series found
            latest = search.results[0]
            latest_date = datetime.datetime.strptime(latest['first_air_date'],
                '%Y-%m-%d').date()
            for result in search.results:
                date = datetime.datetime.strptime(result['first_air_date'],
                    '%Y-%m-%d').date()
                if date > latest_date:
                    latest = result
                    latest_date = date
            logging.debug('TMDB returned: {}, original was: {}'.format(
                latest['name'], series_name))
            name = latest['name']
        except MediaNotFoundInTMDBException:
            search = None
            name = series_name

        logging.info('Torrent is TV series: {}, episode {}'.format(name,
                episode))
        sort_episode(name, episode, torrent_path)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python {} <torrent_id> <torrent_name> <torrent_path>"
                .format(sys.argv[0]))
        sys.exit(1)

    deluge(sys.argv[1], sys.argv[2], sys.argv[3])
