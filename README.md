# YT-Cache

A set of utilities I use to keep copies of my favorite YouTube series.

**Currently only in use for any channel(s) I am also supporting on Patreon**

## check_feed.py

This is the primary script -- It is a simple one intended to use a YouTube channel as an RSS feed.  
It is intended to be run as a CRON Job every so often, and it checks the latest uploaded videos on a 
channel.  If any of the new videos' titles match a predefined set of regexes (in the config file), it
will download those videos.  All videos it parses are added to a list of checked IDs so that repeats are
not downloaded.

The script is designed to output all the videos to a shared folder (for use in a VM, etc), and provides logs 
in `yt-cache.log` within that same shared folder.

## channel_explorer.py

This is a secondary script -- although much longer, it's not intended to be used often after everything 
is setup.

It provides a nice CLI interface using Bullet, where it checks the same config file as `check_feed.py` for 
channels to view.  It uses YouTube's developer API to query for Playlists to display.  The user can then select 
through playlists and videos to decide what videos from the catalog to be downloaded, and it asks for a 
folder (in the same shared folder as `check_feed.py`!) to save the videos into.

The script will also ask you during checks if you would like to add the Playlist that you're downloading from 
into the config JSON file for future monitoring

This script also provides logs in the same shared folder in `yt-channels.log`

## Usage of this project

For any new channel you want to work with, you can just run `init_channel.py` -- this will prompt you 
for some information, and then initialize a new channel in the config JSON file for you.

The idea is that once you have downloaded the back-catalog for a series using `channel_explorer.py`, 
you just enable the series in the config JSON file by either accepting the prompt for doing so inside 
`channel_explorer.py`, or by adding an entry in the `series_to_check` list for the channel in the config
JSON file, and the `check_feed.py` script will take it from there and get each new video as it gets released.
