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
DEBUG = True
# Target directories
MOVIE_DIR  = Path('Movies/')
SERIES_DIR = Path('TV Shows/')
MUSIC_DIR  = Path('Music/')
KEEP_ORIGINAL = True # Set false to remove from download directory

### Constants ###
ANY_MEDIA = 0
TV_MEDIA  = 1
AUDIO_FILES = ('wav', 'mp3', 'flac', 'ogg', 'm4a')
VIDEO_FILES = ('mkv', 'avi', 'mp4', 'mov', 'mpeg', 'wmv', 'flv', 'm4v')
VIDEO_INDICATORS = ('480p', '720p', '1080p', 'HDTV')

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
    if not DEBUG:
        src.copy(dst)

def unify_case(s):
    special_cases = ('to', 'a', 'from', 'is', 'and', 'the')
    s = s.replace('.', ' ')
    s = ' '.join([w.title() if w.lower() not in special_cases else w.lower()
        for w in s.split()])
    s = s[0].upper() + s[1:]
    return s

def list_files(path, extentions):
    files = [path.listdir('*.' + ext) for ext in extentions]
    files = [f for sublist in files for f in sublist]
    return files

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
        src_file = files[0]
        dst_file = Path(series_dir,
            series_name + ' - ' + episode + files[0].ext)
    else:
        if torrent_path.ext not in VIDEO_FILES:
            logging.warning('Unknown video file extention: {}'.format(
                torrent_path.ext))
        src_file = torrent_path
        dst_file = Path(series_dir, series_name + ' - ' + episode + \
            torrent_path.ext)

    logging.info('Copying single file to destination: {}'.format(
            dst_file))
    copy_file(src_file, dst_file)

def sort_movie(movie_name, movie_year, torrent_path):
    movie_dir = Path(MOVIE_DIR, movie_name + ' (' + movie_year + ')')
    movie_dir.mkdir(True)

    if torrent_path.isdir():
        files = list_files(torrent_path, VIDEO_FILES)
        logging.debug('List of files: {}'.format(files))

        # Remove videos that are not part of the movie
        videos = []
        for f in files:
            if any(n.lower() in f.stem.lower() for n in movie_name.split()):
                videos.append(f)
        if len(videos) < len(files) and len(videos) > 0:
            files = videos

        if len(files) == 0:
            logging.critical('No video files found in movie directory!')
            sys.exit(1)
        elif len(files) == 1:
            src_file = files[0]
            dst_file = Path(movie_dir, movie_name + files[0].ext)
            logging.info('Copying single file to destination: {}'.format(
                dst_file))
            copy_file(src_file, dst_file)
        elif len(files) > 1:
            i = 1
            for f in files:
                dst_file = Path(movie_dir, movie_name + ' - CD' + str(i) + \
                    f.ext)
                logging.info('Copying part {} from {} to {}'.format(i,
                    f, dst_file))
                copy_file(f, dst_file)
    else:
        if torrent_path.ext not in VIDEO_FILES:
            logging.warning('Unknown video file extention: {}'.format(
                torrent_path.ext))
        src_file = torrent_path
        dst_file = Path(movie_dir, movie_name + torrent_path.ext)
        logging.info('Copying single file to destination: {}'.format(
            dst_file))
        copy_file(src_file, dst_file)

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

def filter_results_by_name(results, orig_name):
    """Remove results that have a longer title than the original"""
    if len(results) <= 1:
        return results

    logging.info('Removing items from search results by name')
    res = []
    for result in results:
        name = result['title'] if 'title' in result else result['name']
        if all([w in orig_name.lower() for w in name.lower()]):
            res.append(result)
        else:
            logging.debug('Mismatching name "{}", removing'.format(name))
    return res

def filter_results_by_year(results, year):
    if len(results) <= 1:
        return results

    logging.debug('Removing items from search results by year released')
    res = []
    for result in results:
        date = result['release_date'] if 'release_date' in result else \
            result['first_air_date']
        if year in date:
            res.append(result)
        else:
            logging.debug('Invalid year for "{}", removing'.format(
                result['title'] if 'title' in result else result['name']))
    return res

def select_newest_result_by_air_date(results):
    logging.debug('Selecting item based on its air date')
    latest = results[0]
    latest_date = datetime.datetime.strptime(latest['first_air_date'],
        '%Y-%m-%d').date()
    for result in results:
        if 'first_air_date' not in result or result['first_air_date'] == '':
            continue
        date = datetime.datetime.strptime(result['first_air_date'],
            '%Y-%m-%d').date()
        if date > latest_date:
            latest = result
            latest_date = date
    return latest

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
    serie_re = re.compile(r'([\w.]+)(?=(S\d{2}E\d{2}|\d{1,2}x{\d{1,2}))(\2)*')
    series_match = serie_re.match(raw_name)
    if series_match:
        series_name = series_match.group(1).replace('.', ' ').strip()
        episode = series_match.group(2)

        # Get information from TMDB about the series
        try:
            search, name = find_media(series_name, TV_MEDIA)

            # Reduce the results from the TMDB search to one final answer
            # Use the newest series found
            latest = select_newest_result_by_air_date(search.results)
            logging.debug('TMDB returned: {}, original was: {}'.format(
                latest['name'], series_name))
            name = latest['name']
        except MediaNotFoundInTMDBException:
            search = None
            name = series_name

        # Normalise the episode number
        episode_re = re.compile(r'\w?(\d+)\w?(\d+)')
        episode_match = episode_re.match(episode)
        if episode_match:
            serie_nr = episode_match.group(1)
            episode_nr = episode_match.group(2)
            episode = 'S'
            if len(serie_nr) < 2: # Series number is a single digit
                episode += '0'
            episode += serie_nr + 'E'
            if len(episode_nr) < 2: # Episode number is a single digit
                episode += '0'
            episode += episode_nr
            logging.debug('Series number updated to {}'.format(episode))

        logging.info('Torrent is TV series: {}, episode {}'.format(name,
                episode))
        sort_episode(name, episode, torrent_path)
        logging.info('Done processing torrent')
        sys.exit(0)

    # If it is not a single episode from a TV series then we can check
    # The Movie Database to see if it is a known series or movie
    likely_name = raw_name.lower()
    for sep in VIDEO_INDICATORS:
        likely_name = likely_name.split(sep, 1)[0]
    logging.debug('Reduced name from "{}" to "{}"'.format(raw_name,
        likely_name))
    logging.info('Determining if movie/series based on file name')

    try:
        search, name = find_media(likely_name)

        results = filter_results_by_name(search.results, raw_name)
        # If there are still too many titles remove those with dates that
        # don't match with those in the filename
        if len(results) > 1:
            date_match = re.search(re.compile(r'(\d{4})'), raw_name)
            if date_match:
                date = date_match.group(1)
                results = filter_results_by_year(results, date)

        # There are no more methods to reduce the options, so if there are
        # still too many we have failed
        if len(results) > 1:
            logging.error('There are too many video results for torrent_name')
            sys.exit(3)

        result = results[0]
        if result['media_type'] == 'movie':
            logging.info('Media is a movie')
            sort_movie(result['title'], result['release_date'][:4],
                torrent_path)
        elif result['media_type'] == 'tv':
            logging.info('Media is a TV series')
    except MediaNotFoundInTMDBException:
        logging.info('Media not found in TMDB, it is likely audio')
        sys.exit(2)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python {} <torrent_id> <torrent_name> <torrent_path>"
                .format(sys.argv[0]))
        sys.exit(1)

    deluge(sys.argv[1], sys.argv[2], sys.argv[3])
