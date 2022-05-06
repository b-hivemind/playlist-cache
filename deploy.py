from playlist_cache import PlaylistCache

# Make an API request to config service
# GET the defaiult config
# Drop a config.json file 

# Any other init tasks

cache = PlaylistCache()
if cache.active:
    cache.start()
    

