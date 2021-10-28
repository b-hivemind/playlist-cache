import logging as log

from auth_credentials import client_id, client_secret

import spotipy
from spotipy.oauth2 import SpotifyOAuth

redirect_uri = 'http://localhost:8080/'

def login(scope):
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,client_secret=client_secret, redirect_uri=redirect_uri, scope=scope))
        log.info("Successfully logged in")
        return sp 
    except spotipy.oauth2.SpotifyOauthError as e:
        log.error(f"Authentication failed: {e}")
        return None