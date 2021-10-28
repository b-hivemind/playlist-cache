import os, sys
from datetime import datetime

from playlist_cache_oop import PlaylistCache
from playlist_cache_lib import read_config
from auth import login
from scopes import ALL_PLAYLIST_MODIFY_SCOPES, ALL_PLAYLIST_READ_SCOPES, RECENTLY_PLAYED_SCOPE, TOP_READ_SCOPE


class PlaylistCacheController:
    def __init__(self, parent_id, exists=None, start=True):
        self.parent_id = parent_id
        self.cache = None
        self.cache = PlaylistCache(self.parent_id, cache_id=exists)
        self.status = "Ready"        
        self.start_time = None
        if start:
            self.start()
    
    def start(self):
        if not self.status == "Ready":
            return False
        self.start_time = datetime.now()
        self.status = "Running"
        self.cache.start()
        self.status = "Finished"


usage = "USAGE: playlis_cache_factory <parent_id> command"

caches = read_config(sub="caches")

if not sys.argv[1]:
    print("No parent_id provided")  
    print(usage)
    sys.exit(-1)

if sys.argv[1] == "ls":
    print(f"Found {len(caches)} caches")
    sys.exit(0) 

parent_id = sys.argv[1]

if not sys.argv[2]:
    print("No command provided")
    print(usage)
    print("Where command = ['start']")
    sys.exit(-1)
exists = None
if parent_id in caches.keys():
    exists = caches.get(parent_id).get('cache_id')

controller = PlaylistCacheController(parent_id, exists=exists)

command = sys.argv[2]
if command == "start":
    controller.start()


        
        


