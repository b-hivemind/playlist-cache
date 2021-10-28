import unittest
import os, shutil
import json
from unittest.case import expectedFailure

from spotipy.client import SpotifyException

from playlist_cache_lib import *
from auth import login
from scopes import test_scopes

class TestPlaylistCache(unittest.TestCase):
    def setUp(self):
        scope = " ".join([scope for scope in test_scopes])
        self.client = login(scope)
        if not self.client:
            self.fail("Authentication failed")
        self.parent_id = "3Nv1KbnbIUaBZizdZmLcIZ"   # Sunday Morning Breakfast Run
        self.test_config = "test_config.json"
        self.created_material = {
            "playlists": []
        }
    
    def tearDown(self) -> None:
        for type, created_material in self.created_material.items():
            if type == "playlists":
                for playlist in created_material:
                    try:
                        self.client.current_user_unfollow_playlist(playlist)
                    except SpotifyException as e:
                        print(f"[ERROR] [Teardown] Encountered the following error when deleting playlist {playlist}: {e}")
        # Roll test config
        os.remove(self.test_config)
        shutil.copyfile("config.json.bak", self.test_config)
        return super().tearDown()

    def test_create_cache_playlist(self):
        created_playlist_id = create_cache_playlist(self.client, self.parent_id, config=self.test_config)
        self.assertIsNotNone(created_playlist_id)
        self.created_material["playlists"].append(created_playlist_id)
    
    def test_read_config(self):
        with open(self.test_config, 'r') as infile:
            expected_config = json.load(infile)
        self.assertEqual(expected_config, read_config(config=self.test_config, sub=None))
        self.assertEqual(expected_config["global_settings"], read_config(config=self.test_config, sub="global_settings"))
        self.assertEqual(expected_config["caches"]["sample_parent_id"], read_config(config=self.test_config, sub="caches", parent_id="sample_parent_id"))
        expected_tuple = (expected_config, expected_config["caches"]["sample_parent_id_2"])
        self.assertEqual(expected_tuple, read_config(config=self.test_config, parent_id="sample_parent_id_2", sub="caches", write=True))
        expected_tuple = (expected_config, expected_config["global_settings"])
        self.assertEqual(expected_tuple, read_config(config=self.test_config, sub="global_settings", parent_id="sample_parent_id_2", write=True))
        self.assertEqual(expected_tuple, read_config(config=self.test_config, parent_id="sample_parent_id_2", write=True))

    def test_update_config(self):
        update_cache_config(self.parent_id, config=self.test_config, parent_name="Test Parent", cache_id="Test Cache ID", minlen=5, active=False)
        expected_config = {
                "parent_name": "Test Parent",
                "cache_id": "Test Cache ID",
                "long_term_top_tracks": False,
                "cache_minimum_size": 5,
                "interval": 3600,
                "active": False
        }
        received_config = read_config(config=self.test_config, sub="caches", parent_id=self.parent_id)
        self.assertEqual(expected_config, received_config)
    
    def test_get_playlist_track_ids(self):
        self.assertGreater(len(get_playlist_track_ids(self.client, self.parent_id)), 0)

    def test_get_top_tracks(self):
        top_tracks = get_top_tracks(self.client)
        self.assertGreater(len(top_tracks), 0)
        self.assertGreater(len(get_top_tracks(self.client, long=True)), len(top_tracks))
    
    def test_get_recents(self):
        self.assertGreater(len(get_recents(self.client)), 0)
    
    def test_fetch_common_tracks(self):
        recently_played = get_recents(self.client)
        update_cache_config("sample_parent_id", config=self.test_config, long=True)
        top_tracks = get_top_tracks(self.client, long=True)
        expected_tracks = top_tracks.union(recently_played)
        self.assertEqual(expected_tracks, fetch_user_common_tracks(self.client, "sample_parent_id", self.test_config))

        update_cache_config("sample_parent_id", config=self.test_config, long=False)
        top_tracks = get_top_tracks(self.client)
        expected_tracks = top_tracks.union(recently_played)
        self.assertEqual(expected_tracks, fetch_user_common_tracks(self.client, "sample_parent_id", self.test_config))
        
if __name__ == '__main__':
    unittest.main(verbosity=2)