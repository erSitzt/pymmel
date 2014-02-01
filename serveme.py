from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import HTTPServer
from StringIO import StringIO
import subprocess
import os
import threading
import urlparse
import cgi
import re
import urllib2
import pipes
import tempfile
import Queue
import time

#import alsaaudio

class MyRequestHandler(SimpleHTTPRequestHandler):

    #mixer = alsaaudio.Mixer("PCM")
    playing = 0
    #volume = mixer.getvolume()[0]
    #mute = mixer.getmute()[0]
    process = None
    tempplaylistfile = None

    def do_POST(self):
        """Respond to a POST request."""
        # Extract and print the contents of the POST
        length = int(self.headers['Content-Length'])
        post_data = urlparse.parse_qs(self.rfile.read(length))
        
        if post_data['action'][0] == "play":
            #self.startProcess(self,post_data['title'][0])
            OMXThread.Actions.put({"play" : post_data['title'][0]})
        elif post_data['action'][0] == "queue":
            MyRequestHandler.tempplaylistfile = tempfile.NamedTemporaryFile('w+b', -1 ,'.m3u')
            MyRequestHandler.tempplaylistfile.write(str(post_data['title'][0])+'\n')
            print "Queue " + post_data['title'][0]
            OMXThread.Playlist.put(post_data['title'][0])
            OMXThread.Actions.put({"queue" : post_data['title'][0]})
        if MyRequestHandler.process is not None:
            MyRequestHandler.process.poll()
            print "RETCODE : " + str(MyRequestHandler.process.returncode)
            if MyRequestHandler.process.returncode is None:
                if post_data['action'][0] == "stop":
                        stop = MyRequestHandler.process.stdin.write('p')
                elif post_data['action'][0] == "mute":
                        MyRequestHandler.process.stdin.write('-')
                elif post_data['action'][0] == "volup":
                        MyRequestHandler.process.stdin.write('+')
                elif post_data['action'][0] == "voldown":
                        MyRequestHandler.process.stdin.write('-')
                elif post_data['action'][0] == "back":
                        MyRequestHandler.process.stdin.write("\x1B[B")
                elif post_data['action'][0] == "forward":
                        MyRequestHandler.process.stdin.write("\x1B[A")
                elif post_data['action'][0] == "smallforward":
                        MyRequestHandler.process.stdin.write("\x1B[C")
                elif post_data['action'][0] == "smallback":
                        MyRequestHandler.process.stdin.write("\x1B[D")

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()


    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            return self.list_directory(path)

        return f

    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).

        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().

        """

        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        list.sort(lambda a, b: cmp(a.lower(), b.lower()))

        self.path = urlparse.urlparse(self.path).path

        f = StringIO()
        f.write('<meta name="viewport" content="width=device-width, initial-scale=1.0">')

        f.write('<link href="//netdna.bootstrapcdn.com/bootstrap/3.0.3/css/bootstrap.min.css" rel="stylesheet">')
        f.write('<link href="//netdna.bootstrapcdn.com/font-awesome/4.0.3/css/font-awesome.min.css" rel="stylesheet">')
        f.write('<script src="//code.jquery.com/jquery-2.0.3.min.js"></script>')
        f.write('<script src="//netdna.bootstrapcdn.com/bootstrap/3.0.3/js/bootstrap.min.js"></script>')
        f.write('<script>$(document).ready(function(){\
            $(".btn").click(function(){\
                var clickedID = this.id;\
                if (this.name == "play")\
                {\
                    $.post( "/", { action: "play", title: this.id } );\
                    $("#nowplaying").html(this.id);\
                }\
                else if (this.name == "queue")\
                {\
                    $.post( "/", { action: "queue", title: this.id } );\
                }\
                else if (this.name == "stop")\
                {\
                	$(this).find("span").toggleClass("glyphicon glyphicon-pause glyphicon glyphicon-play");\
                    $.post( "/", { action: "stop" } );\
                }\
                else if (this.name == "mute")\
                {\
                    $.post( "/", { action: "mute" } );\
                }\
                else if (this.name == "volup")\
                {\
                    $.post( "/", { action: "volup" } );\
                }\
                else if (this.name == "voldown")\
                {\
                    $.post( "/", { action: "voldown" } );\
                }\
                else if (this.name == "back")\
                {\
                    $.post( "/", { action: "back" } );\
                }\
                else if (this.name == "forward")\
                {\
                    $.post( "/", { action: "forward" } );\
                }\
                else if (this.name == "smallforward")\
                {\
                    $.post( "/", { action: "smallforward" } );\
                }\
                else if (this.name == "smallback")\
                {\
                    $.post( "/", { action: "smallback" } );\
                }\
                \
                });\
            })</script>')
        f.write("<title>Directory listing for %s</title>\n" % self.path)
        f.write('<div class="container">')
        f.write('<div class="row">')
        f.write('<div class="col-xs-12">')
        f.write('<div class="panel panel-default">')
        f.write('<div class="panel-heading"><span class="label label-default">%s</span></div>\n' % (self.path))
        f.write('<div class="panel-body"><span class="badge"><span id="nowplaying">%s</span></span><div class="btn-group pull-right">\
            <button type="button" name="back" class="btn btn-primary "><span class="glyphicon glyphicon-fast-backward" id="back"></span></button>\
            <button type="button" name="smallback" class="btn btn-primary "><span class="glyphicon glyphicon-backward" id="smallback"></span></button>\
            <button type="button" name="smallforward" class="btn btn-primary "><span class="glyphicon glyphicon-forward" id="smallforward"></span></button>\
            <button type="button" name="forward" class="btn btn-primary "><span class="glyphicon glyphicon-fast-forward" id="forward"></span></button>\
            <button type="button" name="stop" class="btn btn-primary "><span class="glyphicon glyphicon-stop" id="stop"></span></button>\
            <button type="button" name="volup" class="btn btn-primary "><span class="glyphicon glyphicon-volume-up"></span></button>\
            <button type="button" name="voldown" class="btn btn-primary "><span class="glyphicon glyphicon-volume-down"></span></button>\
            <button type="button" name="mute" class="btn btn-primary"><span class="glyphicon glyphicon-volume-off"></span></button></div></div>' % (self.playing))
        f.write('<ul class="list-group">\n')
        currentpath = urlparse.urlparse(self.path).path
        currentpath = re.sub("/$", "", currentpath)
        dirup, removed = os.path.split(currentpath)
        f.write('<b><a href="%s" class="list-group-item">.. up one directory</a></b>\n' % (dirup))
        for name in list:
            if not name.startswith('.'):
                #print "PATH : " + path + " NAME : " + name
                fullname = os.path.join(path, name)
                displayname = linkname = name = cgi.escape(name)
                parsed_path = urlparse.urlparse(self.path)
                # Append / for directories or @ for symbolic links
                dir = False
                link = False
                if os.path.isdir(fullname):
                    displayname = name + "/"
                    linkname = name + "/"
                    dir = True
                if os.path.islink(fullname):
                    displayname = name + "@"
                    link = True
                    # Note: a link to a directory displays with @ and links with /
                if (dir or link):
                    f.write('<a href="%s" class="list-group-item"><b>%s</b></a>\n' % (linkname, displayname))
                else:
                    if os.path.splitext(name)[-1].lower() in ('.mp3', '.mp4', '.mkv', '.mpg', '.avi', '.wmv'):
                        if parsed_path.query:
                            f.write('<li class="list-group-item"><span>%s</span><i class="glyphicon glyphicon-time></a><button type="button" id="mama" class="btn btn-default btn-xs pull-right">enqueue</button></li>\n' % (self.path, displayname))
                        else:
                            #f.write('<a href="%s?play=%s" class="list-group-item">%s <span class="glyphicon glyphicon-time"></span></a><button type="button" class="btn btn-default btn-xs pull-right">enqueue</button>\n' % (self.path, fullname, displayname))
                            f.write('<li class="list-group-item">%s<div class="btn-group pull-right"><button type="button" name="play" id="%s" class="btn btn-success"><span class="glyphicon glyphicon-play"></span></button><button type="button" name="queue" id="%s" class="btn btn-default queue"><span class="glyphicon glyphicon-time"></span></button></div></li>\n' % (displayname, fullname, fullname))
        f.write("</ul>\n")
        f.write("</div>\n")
        f.write("</div>\n")
        f.write("</div>\n")
        f.write("</div>\n")
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        return f

    def teststartProcess(self, name, path):
        """
        Starts a process in the background and writes a PID file

        returns integer: pid
        """

        pathname, filename = os.path.split(path)
        MyRequestHandler.playing = filename
        #self.stopAllPlayers()
        if MyRequestHandler.process is not None:
            MyRequestHandler.process.poll()
            print "RETCODE2 : " + str(MyRequestHandler.process.returncode)
            if MyRequestHandler.process.returncode is None:
                MyRequestHandler.process.stdin.write('q')
                MyRequestHandler.process = None
        ext = os.path.splitext(path)[-1].lower()
        if ext in ('.mp4', '.mkv', '.mpg', '.avi', '.wmv', '.mp3', '.wav'):
            print "omxplayer " + path
            MyRequestHandler.process = subprocess.Popen(['/usr/bin/omxplayer' , path] , stdin=subprocess.PIPE, shell=False)
        return 1

    def stopAllPlayers(self):
        os.system('pkill omxplayer.bin')

class OMXThread(threading.Thread):
    Actions = Queue.Queue()
    Playlist = Queue.Queue()

    omxprocess = None

    def run(self):
        while True:
            if OMXThread.omxprocess is not None:
                OMXThread.omxprocess.poll()
                if OMXThread.omxprocess.returncode is not None:
                    print "titel zu ende!"
                    try:
                        title = OMXThread.Playlist.get(False)
                    except Queue.Empty:
                        pass
                    else:
                        print title
                        self.startProcess(title)
                        OMXThread.Playlist.task_done()

            try:
                action = OMXThread.Actions.get(False)
            except Queue.Empty:
                pass
            else:
                print action
                if "play" in action:
                    self.startProcess(action["play"])

                OMXThread.Actions.task_done()
            time.sleep(1)




    def startProcess(self, path):
        """
        Starts a process in the background and writes a PID file

        returns integer: pid
        """

        pathname, filename = os.path.split(path)
        MyRequestHandler.playing = filename
        #self.stopAllPlayers()
        if MyRequestHandler.process is not None:
            MyRequestHandler.process.poll()
            print "RETCODE2 : " + str(MyRequestHandler.process.returncode)
            if MyRequestHandler.process.returncode is None:
                MyRequestHandler.process.stdin.write('q')
                MyRequestHandler.process = None
        ext = os.path.splitext(path)[-1].lower()
        if ext in ('.mp4', '.mkv', '.mpg', '.avi', '.wmv', '.mp3', '.wav'):
            print "omxplayer " + path
            OMXThread.omxprocess = subprocess.Popen(['/usr/bin/omxplayer' , path] , stdin=subprocess.PIPE, shell=False)
        return 1

thread = OMXThread()
thread.setDaemon(True)
thread.start()

server = HTTPServer(("0.0.0.0", 8001), MyRequestHandler)
server.serve_forever()
