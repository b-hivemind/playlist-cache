from datetime import datetime
import time
import sys
import logging as log

from spotipy.client import SpotifyException

from lib import *
from auth.oauth import login
from auth.scopes import ALL_PLAYLIST_MODIFY_SCOPES, ALL_PLAYLIST_READ_SCOPES, RECENTLY_PLAYED_SCOPE, TOP_READ_SCOPE



class PlaylistCache:
    def __init__(self):
        log.basicConfig(filename=f"/var/log/playlist_cached.log", level=log.INFO, format='[%(levelname)s] [%(asctime)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        
        self.parent_id = None
        self.cache_id = None
        self.active = False
        self.client = None
        self.config = { "active": False }

        self.update()
        
        if not self.active or not self.parent_id:
            log.error("Config: {}".format(self.config))
            sys.exit(-1)
            
    def update(self):
        self.config = read_config()
        self.parent_id = self.config.get("parent_id")
        self.cache_id = self.config.get("cache_id")
        self.active = self.config.get("active")
    

    def monitor(self):
        log.debug("Begin monitor")
        # Re-authorize on every run
        if not self.client:
            self.client = login(" ".join([ALL_PLAYLIST_MODIFY_SCOPES, ALL_PLAYLIST_READ_SCOPES, RECENTLY_PLAYED_SCOPE, TOP_READ_SCOPE]))
        if not self.client:
            log.error("Authorization Error")
            sys.exit(-1)
        
        cache_playlist = None
        for i in range(3):
            try:
                # First, ping to check if the cache has been deleted
                cache_playlist = self.client.playlist(self.cache_id)
                break
            except SpotifyException as e:
                log.error(e)
                continue
    
        if not cache_playlist:        
            # Playlist has been deleted, create a new one
            self.cache_id = create_cache_playlist(self.client, self.parent_id)
            self.update()
            
        
        log.debug("Fetching parent track ids")
        source_track_ids = set(get_playlist_track_ids(self.client, self.parent_id))
        
        for playlist_id in self.config.get("alt_sources", []):
            source_track_ids = source_track_ids.union(get_playlist_track_ids(self.client, playlist_id))

        log.debug("Fetching cache track ids")
        cache_track_ids = set(get_playlist_track_ids(self.client, self.cache_id))

        most_played_track_ids = fetch_user_common_tracks(self.client, self.parent_id)
        common_tracks = source_track_ids.intersection(most_played_track_ids)
        new_tracks = common_tracks - cache_track_ids
        if new_tracks:
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
                while len(cache_track_ids - extras) > self.config.get("minimum_size", 0) and len(extras) > 0:
                    tracks_to_remove.append(extras.pop())
                log.info(f"Removing tracks {[self.client.track(i)['name'] for i in tracks_to_remove]}")
                self.client.playlist_remove_all_occurrences_of_items(self.cache_id, tracks_to_remove)
            except SpotifyException as e:    
                log.error(f"{e}")
        else:
            log.debug("No new tracks found")
        
        # Delete the client instance
        self.client = None    
        log.debug("End monitor")
        
    def start(self):
        while True:
            self.update()
            self.monitor()
            log.info(f"Sleeping for {self.config.get('interval')}")
            time.sleep(self.config.get("interval", 60 * 60 * 24))
        self.active = False

    
