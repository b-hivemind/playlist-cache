from datetime import datetime
import time
import sys
import logging as log

from spotipy.client import SpotifyException

from playlist_cache_lib import *
from auth import login
from scopes import ALL_PLAYLIST_MODIFY_SCOPES, ALL_PLAYLIST_READ_SCOPES, RECENTLY_PLAYED_SCOPE, TOP_READ_SCOPE



class PlaylistCache:
    def __init__(self, parent_id, spotipy_client=None, cache_id=None, config_file="config.json"):
        self.client = spotipy_client
        log.basicConfig(filename=f"logs/{parent_id}", level=log.INFO, format='[%(levelname)s] [%(asctime)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        log.basicConfig(filename=f"logs/debug/{parent_id}", level=log.DEBUG, format='[%(levelname)s] [%(asctime)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        if not self.client:
            self.client = login(" ".join([ALL_PLAYLIST_MODIFY_SCOPES, ALL_PLAYLIST_READ_SCOPES, RECENTLY_PLAYED_SCOPE, TOP_READ_SCOPE]))
        if not self.client:
            log.error("Authorization Error")
            sys.exit(-1)
        self.parent_id = parent_id
        self.cache_id = cache_id
        self.long = False
        self.minlen = 0
        self.config_file = config_file
        self.interval = 60 * 60 * 1 # 1 Hour
        self.active = True

        if not self.cache_id:
            self.cache_id = create_cache_playlist(self.client, self.parent_id)
        else:
            self.read_config()
        if not self.cache_id:
            raise "Check logs for error"
    
    def read_config(self):
        config = read_config(config=self.config_file, sub="caches", parent_id=self.parent_id)
        self.cache_id = config.get("cache_id")
        self.long = config.get("long_term_top_tracks", False)
        self.minlen = config.get("cache_minimum_size", 0)
        self.interval = config.get("interval", 3600)
        self.active = config.get("active", False)
    

    def monitor(self):
        log.debug("Begin monitor")
        # Re-authorize on every run
        try:
            if not self.client:
                self.client = login(" ".join([ALL_PLAYLIST_MODIFY_SCOPES, ALL_PLAYLIST_READ_SCOPES, RECENTLY_PLAYED_SCOPE, TOP_READ_SCOPE]))
            if not self.client:
                log.error("Authorization Error")
                sys.exit(-1)
        
            # First, ping to check if the cache has been deleted
            cache_playlist = self.client.playlist(self.cache_id)
            
            user_playlists = [playlist['id'] for playlist in get_user_playlists(self.client)]
    
            if not cache_playlist or not self.cache_id in user_playlists:
                # Playlist has been deleted, create a new one
                self.cache_id = create_cache_playlist(self.client, self.parent_id)
                self.read_config()
            
        
            log.debug("Fetching parent track ids")
            parent_track_ids = set(get_playlist_track_ids(self.client, self.parent_id))
            log.debug("Fetching cache track ids")
            cache_track_ids = set(get_playlist_track_ids(self.client, self.cache_id))

            most_played_track_ids = fetch_user_common_tracks(self.client, self.parent_id, self.config_file)
            common_tracks = parent_track_ids.intersection(most_played_track_ids)
            new_tracks = common_tracks - cache_track_ids
            log.info("Unique tracks {}".format(new_tracks))
        
                
            # If no common tracks are found, maintain the same state (don't delete tracks)
            if common_tracks != set():
                try:
                    log.info(f"Adding tracks {[self.client.track(x)['name'] for x in new_tracks]}")
                    if len(new_tracks) > 0:
                        self.client.playlist_add_items(self.cache_id, new_tracks)   
                    # Delete tracks no longer commonly played if more tracks than required
                    extras = cache_track_ids - common_tracks
                    tracks_to_remove = []
                    if len(cache_track_ids) > self.minlen and len(extras) > 0:    
                        while len(cache_track_ids - extras) > self.minlen and len(extras) > 0:
                            tracks_to_remove.append(extras.pop())
                    log.info(f"Removing tracks {[self.client.track(i)['name'] for i in tracks_to_remove]}")
                    self.client.playlist_remove_all_occurrences_of_items(self.cache_id, tracks_to_remove)
                except SpotifyException as e:    
                    log.error(f"{e}")
            else:
                log.debug("No new tracks found")
        
            # Delete the client instance
            self.client = None    
            log.debug"End monitor")
        # TODO remove broad except 
        except Exception as e:
            log.error(e)

    def start(self):
        while self.active:
            self.read_config()
            self.monitor()
            log.info(f"Sleeping for {self.interval}")
            time.sleep(self.interval)

    
