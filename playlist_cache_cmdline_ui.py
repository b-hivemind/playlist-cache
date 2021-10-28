import sys
import os
import json
import subprocess

from playlist_cache_lib import get_user_playlists
from auth import login
from scopes import ALL_PLAYLIST_READ_SCOPES
from playlist_cache_oop import PlaylistCache


def generic_menu(iterable, title=None, quit=True):
    """
    Parameters:
        iterable  - [list of {Spotipy dicts with 'name' field}] 
                     * usually collections of playlists
                     * prints the Spotipy object/dict otherwise
        title     - string
                     * Title for the menu
        enumerate - boolean
                     * Returns a tuple with the index and the 
                       associated object
    Returns:    
        None      - If option is EXIT
        obj       - The object the user selected
        (i, obj)  - where i is the index (option - 1) and obj is
                    the associated object
    """             
    EXIT = 'e'
    print(title)
    option = None
    for i, v in enumerate(iterable):
        print(f"[{i+1}]: {v.get('name', v)}")
    print(f"------------------\n[{EXIT}]xit")
    while not option:
        option = input("[Enter Number]=> ")
        if option.lower() == EXIT:
            return None
        try:
            obj = iterable[int(option)-1]
        except IndexError:
            print(f"Invalid option {option}")
            continue
        except ValueError:
            print(f"Invalid option {option}")
            continue
        return obj

client = login("{}".format(ALL_PLAYLIST_READ_SCOPES))
if not client:
    print("Authorization error")
    sys.exit(-1)

all_playlists = get_user_playlists(client)
if len(all_playlists) == 0:
    print("Error getting playlists. Got 0 results")
    sys.exit(-1)

parent_playlist = generic_menu(all_playlists, title="Choose playlist to cache")
if not parent_playlist:
    print("No playlist chosen")
    sys.exit(-1)
parent_playlist_id = parent_playlist.get("id", parent_playlist.get("uri", None))
subprocess.Popen(["python", "playlist_cache_factory.py", f"{parent_playlist_id}", "start"])