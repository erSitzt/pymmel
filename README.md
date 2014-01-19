pymmel
======

Micro mediacenter w. webinterface for raspberry pi without an X-server
Webinterface using twitter bootstrap.

This is only a slightly modified version of the SimpleHTTPServer that can be run by python out of the box, serving you files from the directory you started it in.

First off, i'm new to python and i never did any web-stuff, so most of what i'm doing might be wrong or even dangerous :)
I use this to play music on my stereo and start movies to watch on my tv/beamer... it works, goal reached :)
You probably should not make this accessible from the internet !?!ß!

Requirements:
* Python 2.7
* python-alsaaudio
* omxplayer (for fullhd framebuffer video)
* mpg123 (for music)
* maybe more :)

The programs used for video, music or any additional types of files can be altered quite easily

TODO:
* Playlist
* wakeup tv/beamer with tvservice
* slideshow for images using fbi or something


Use it as a service with upstart (`apt-get install upstart` and ignore some warnings on raspbian )
create an upstart script  `/etc/init/pymmel.conf`

Change the paths to the basedir where you put serveme.py. Inside that dir you can create symlinks or mount network shares.

`
description "Pymmel Initscript"
author "me"

start on runlevel [2345]
stop on runlevel [!2345]

chdir /home/pi
exec /usr/bin/python /home/pi/test/serveme.py
respawn

`

