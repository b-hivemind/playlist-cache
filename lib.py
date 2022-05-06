import json 
import logging as log
from spotipy.client import SpotifyException

FIXTURES = {
    "description": "This playlist is maintained by my playlist_cache script which runs an hourly job to compare my most \
                    recently played music with the songs in {} and maintain this playlist with any matching tracks. \
                    Currently testing",
    "long_term_top_tracks": False,
    "cache_minimum_size": 0
}
LONG_TERM_TOP_TRACKS = False
CONFIG_NAME = "/config/config.json"
CACHE_MINIMUM_SIZE = 0

def _paged_results(sp, results):
    temp = results['items']
    while results['next']:
        results = sp.next(results)
        temp.extend(results['items'])
    return temp

def create_cache_playlist(sp, parent_id):  
    try:
        parent_playlist = sp.playlist(parent_id)
        parent_playlist_name = parent_playlist.get("name")
        cache_playlist_name = parent_playlist_name + " cache"
        cache_playlist_description = FIXTURES["description"].format(parent_playlist_name)
        cache_playlist_id = sp.user_playlist_create(sp.me()['id'], name=cache_playlist_name, description=cache_playlist_description).get('id')
        update_cache_config(parent_id, cache_id=cache_playlist_id)
        log.info(f"Created playlist {cache_playlist_name} with id {cache_playlist_id}")
        return cache_playlist_id
    except SpotifyException as e:
        log.error(f"{e}")
        return None

def read_config():
    json_config = {}
    with open(CONFIG_NAME, 'r') as readfile:
        json_config = json.load(readfile)
    return json_config


def update_cache_config(parent_id, cache_id=None, long=None, minlen=None, active=None, interval=None):
    config = read_config()
       
    config.update({"cache_id" : (cache_id or config.get("cache_id", ""))})
    config.update({"long_term_top_tracks" : (long if long is not None else config.get("long_term_top_tracks", LONG_TERM_TOP_TRACKS))})
    config.update({"active" : (active if active is not None else config.get("active", True))})

    with open(CONFIG_NAME, 'w') as outfile:
        json.dump(config, outfile, indent="\t")

def get_playlist_track_ids(sp, playlist_id):
    try:
        track_ids = [track['track']['id'] for track in _paged_results(sp, sp.playlist_items(playlist_id))]
        log.debug(f"Found {len(track_ids)} playlist tracks")
        return track_ids
    except SpotifyException as e:
        log.info(f"[ERROR {e}]")
        return []

def get_top_tracks(sp, long=False):
    try:
        short_term_top_track_obj = _paged_results(sp, sp.current_user_top_tracks(time_range='short_term'))
        short_top_tracks = set([track['id'] for track in short_term_top_track_obj])
        log.debug(f"Found {len(short_top_tracks)} short term top tracks")
        log.debug(f"{set([track['name'] for track in short_term_top_track_obj])}")
        med_top_tracks_obj = _paged_results(sp, sp.current_user_top_tracks(time_range='medium_term'))
        med_top_tracks = set([track['id'] for track in med_top_tracks_obj])
        log.debug(f"Found {len(med_top_tracks)} medium term top tracks")
        log.debug(f"{set([track['name'] for track in med_top_tracks_obj])}")
        top_tracks_union = short_top_tracks.union(med_top_tracks)
        if long:
            log.debug("Retrieving long term top tracks...")
            long_term_top_tracks_obj = _paged_results(sp, sp.current_user_top_tracks(time_range='long_term'))
            long_top_tracks = set([track['id'] for track in long_term_top_tracks_obj])
            log.debug(f"Found {len(long_top_tracks)} long term top tracks")
            log.debug(f"{set([track['name'] for track in long_term_top_tracks_obj])}")
            top_tracks_union = top_tracks_union.union(long_top_tracks)
        log.debug(f"Top tracks union contains {len(top_tracks_union)} tracks")
        return top_tracks_union
    except SpotifyException as e:
        log.error(f"{e}")
        return set()

def get_recents(sp):
    try:
        recently_played = _paged_results(sp, sp.current_user_recently_played())
        recently_played_track_ids = set([x['track']['id'] for x in recently_played])
        recently_played_track_names = set([x['track']['name'] for x in recently_played])
        log.debug(f"Found {len(recently_played_track_ids)} recently played tracks")
        log.debug(f"{recently_played_track_names}")
        return recently_played_track_ids
    except SpotifyException as e:
        log.error(f"{e}")
    return set()

def fetch_user_common_tracks(sp, parent_id):
    cache_cnf = read_config() 
    top_tracks = get_top_tracks(sp, long=cache_cnf.get("long_term_top_tracks", False))
    recently_played = get_recents(sp)
    common_tracks = top_tracks.union(recently_played)
    repeat_rewind_id = cache_cnf.get("repeat_rewind_playlist_id")
    if repeat_rewind_id:
        log.debug("Fetching repeat rewind track ids")
        repeat_rewind_track_ids = get_playlist_track_ids(sp, repeat_rewind_id)
        return common_tracks.union(repeat_rewind_track_ids)
    return common_tracks

def get_user_playlists(sp):
    try:
        return _paged_results(sp, sp.current_user_playlists())
    except SpotifyException as e:
        log.error(f"{e}")
        return []

