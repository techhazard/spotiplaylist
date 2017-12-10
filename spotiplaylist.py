#!/usr/bin/python3 -u

import sys
import spotipy
import spotipy.util as util
from itertools import zip_longest

# You get both of these from the spotify API
SPOTIFY_CLIENT_ID="YOUR_CLIENT_ID"
SPOTIFY_CLIENT_SECRET="YOUR_CLIENT_SECRET"

# set this as a valid redirection uri in the API management screen
# (where you got your Client data)
REDIRECT_URI="http://succesful-login.localhost/"

scope = 'playlist-modify-private'



def pick_one(song, results):
    """Return the URI of the best match."""
    # TODO: actually do that
    return results[0]['uri']

def parse_line(line):
    parts = line.split("–", maxsplit=1)
    if len(parts) != 2:
        print(line)
        return {}
    artist = parts[0].strip()
    title = parts[1].strip()
    return {'artist': artist, 'title': title}

def read_songlist(filename):
    with open(filename, "r") as songlist:
        linecount = sum(map(lambda x: 1, songlist.readlines()))
        print("Looking up {} songs".format(linecount))
        if linecount > 100:
            print("Oh man, this is gonna take a while...")

    with open(filename,"r") as songlist:
        for line in songlist:
            yield parse_line(line)


def chunker(iterable, chunksize, fillvalue=""):
    args = [iter(iterable)] * chunksize
    return zip_longest(*args, fillvalue=fillvalue)

def reduce_title(old_title):
    """Strip last word of title"""
    return old_title.split()[:-1]

def reduce_artist(old_artist):
    # replace "bobby ft alice" with "bobby"
    re = r'/(.*)\b(ft|featuring)\b.*$/\1/i'

def do_search(spotify, song):
    searchterm = "{artist} {title}".format(**song)
    try:
        return spotify.search(searchterm, type='track')['tracks']['items']
    except spotipy.client.SpotifyException as ex:
        print("search failed: {artist} – {title}".format(**song))
        print("reason: {}".format(ex))
        return None


if __name__ == "__main__":
    if len(sys.argv) > 2:
        username = sys.argv[1]
        songlist = sys.argv[2]
        playlist_name = songlist
    else:
        print(("Usage: %s username songlist" % (sys.argv[0],)))
        sys.exit(1)

    print("Starting SpotiPlaylist for user {}".format(username))
    token = util.prompt_for_user_token(username, scope,
                                       client_id=SPOTIFY_CLIENT_ID,
                                       client_secret=SPOTIFY_CLIENT_SECRET,
                                       redirect_uri=REDIRECT_URI)
    if token:
        spotify = spotipy.Spotify(auth=token)
        songlist = read_songlist(songlist)
        list_of_songs = []
        for song in songlist:

            result = do_search(spotify, song)

            if result is None:
                continue
            elif len(result) == 1:
                list_of_songs.append(result[0]["uri"])
            elif len(result) > 1:
                list_of_songs.append(pick_one(song, result))
            else:
                print("not found: {artist} – {title}".format(**song))
                # TODO: try again with different search term

        # we create a playlist with the same name as the file
        playlist = spotify.user_playlist_create(user=username, name=playlist_name, public=False)

        # we add our list of songs to it
        # we do it in chunks, because otherwise it breaks
        for partial_list in chunker(list_of_songs, 50):

            result = spotify.user_playlist_add_tracks(user=username, playlist_id=playlist['id'],tracks=filter(lambda x: x != "", partial_list))

        print("Playlist {} created!".format(playlist_name))
        sys.exit(0)
    else:
        print("Can't get token for", username)

