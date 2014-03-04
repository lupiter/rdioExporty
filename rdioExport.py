
from __future__ import unicode_literals, absolute_import
import requests
from requests_oauthlib import OAuth1Session
import sys
import os
import os.path
import keyring

git_sub_modules = './' #Relative paths ok too
for dir in os.listdir(git_sub_modules):
    path = os.path.join(git_sub_modules, dir)
    if not path in sys.path:
        sys.path.append(path)

from pyItunes import *

rdioURL = "http://api.rdio.com/1/"
request_token_url = "http://api.rdio.com/oauth/request_token"
base_authorization_url = "https://www.rdio.com/oauth/authorize"
access_token_url = "http://api.rdio.com/oauth/access_token"

client_key = "jbu8brgbmq63qazzvttsnv5g"
client_secret = "U2HTvUraQ8"

class CommonEqualityMixin(object):

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

class Song(CommonEqualityMixin):
    def __init__(self, title, album="", artist="", playCount=0):
        self.title = title
        self.album = album
        self.artist = artist
        self.playCount = playCount

    def __unicode__(self):
        return "{0.title},{0.artist},{0.album}".format(self)

    def __repr__(self):
        return self.__unicode__()



def authenticate():
    oauth = OAuth1Session(client_key, client_secret=client_secret, callback_uri="oob")

    fetch_response = oauth.fetch_request_token(request_token_url)
    resource_owner_key = fetch_response.get('oauth_token')
    resource_owner_secret = fetch_response.get('oauth_token_secret')
    authorization_url = oauth.authorization_url(base_authorization_url)
    print 'Please go here and authorize,', authorization_url
    verifier = raw_input('Paste the PIN here: ')

    rdio = OAuth1Session(client_key,
                client_secret=client_secret,
                resource_owner_key=resource_owner_key,
                resource_owner_secret=resource_owner_secret,
                verifier=verifier)

    oauth_tokens = rdio.fetch_access_token(access_token_url)
    keyring.set_password("rdioExporty", "token", oauth_tokens['oauth_token'])
    keyring.set_password("rdioExporty", "secret", oauth_tokens['oauth_token_secret'])
    return rdio

def reAuthenticate():
    rdio = None
    token = keyring.get_password("rdioExporty", "token")
    secret = keyring.get_password("rdioExporty", "secret")
    if token is not None and secret is not None:
        rdio = OAuth1Session(client_key,
                      client_secret=client_secret)
        rdio._populate_attributes({'oauth_token': token,
                      'oauth_token_secret': secret})
    else:
        rdio = authenticate()
    return rdio


rdio = reAuthenticate()
# rdio = authenticate()

# Get user ID
userIDAns = rdio.post(rdioURL, {'method': "currentUser"})
userJson = None
try:
    userJson = userIDAns.json()
except ValueError:
    print userIDAns
    print userIDAns.text
if userJson['status'] != 'ok':
    print userIDAns
    sys.exit(0)
userID = userJson['result']['key']

# Get rdio songs

songs = rdio.post(rdioURL, {'method': 'getTracksInCollection', 'user': userID, 'sort': 'playCount'}).json()['result']

print "You have {0} tracks in your rdio library.".format(len(songs))

songlist = []
for song in songs:
    newSong = Song(song['name'],song['artist'],song['album'])
    if 'playCount' in song:
        newSong.playCount = song['playCount']
    songlist.append(newSong)


# albumlist = set([(song['artist'].lower(), song['album'].lower()) for song in songs])


# Read iTunes Library

homeDir = os.getenv("HOME")
iTunesDir = os.path.join(homeDir, "Music", "iTunes", "iTunes Music Library.xml")
iLibrary = Library(iTunesDir)

iSonglist = [Song(song[1].name, song[1].artist, song[1].album) for song in iLibrary.songs.items()]
# iAlbumlist = set([(unicode(song[1].album).lower(), unicode(song[1].artist).lower()) for song in iLibrary.songs.items()])

print "You have {0} tracks in your iTunes library.".format(len(iSonglist))

rdioOnly = [x for x in songlist if x not in iSonglist]
itunesOnly = [x for x in iSonglist if x not in songlist]

print "Only in rdio, {0} tracks.".format(len(rdioOnly))
print "Only in iTunes {0} tracks.".format(len(itunesOnly))
print "In both, {0} tracks.".format(len(songlist) - len(rdioOnly))

# print "{0} albums in your rdio library, {1} in your iTunes library, an overlap of {2}".format(len(albumlist),len(iAlbumlist), len(albumlist.intersection(iAlbumlist)))

# for albums in (albumlist - iAlbumlist):
    # print albums

# albumsByArtist = set([])
# for album in albumlist:
#   if album not in iAlbumlist:
#       found = False
#       for alreadyArtist in iter(albumsByArtist):
#           if alreadyArtist[0] == album[0]:
#               found = True
#               albumsByArtist.remove(alreadyArtist)
#               lister = list(alreadyArtist)
#               lister.append(album[1])
#               albumsByArtist.add(tuple(lister))
#       if not found:
#           albumsByArtist.add(album)

# for artist in albumsByArtist:
#   print "{0} : {1}".format(artist[0], ", ".join(artist[1:]))


