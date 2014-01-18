from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import HTTPServer
from StringIO import StringIO
import subprocess
import os
import cStringIO
import urlparse
import cgi
import re
import urllib2
import pipes
import alsaaudio

class MyRequestHandler(SimpleHTTPRequestHandler):

    mixer = alsaaudio.Mixer("PCM")
    playing = 0
    volume = mixer.getvolume()[0]
    mute = mixer.getmute()[0]

    def do_POST(self):
        """Respond to a POST request."""
        # Extract and print the contents of the POST
        length = int(self.headers['Content-Length'])
        post_data = urlparse.parse_qs(self.rfile.read(length))

        if post_data['action'][0] == "play":
            self.startProcess(self,post_data['title'][0])
        elif post_data['action'][0] == "queue":
            print "Queue " + post_data['title'][0]
        elif post_data['action'][0] == "stop":
            self.stopAllPlayers()
        elif post_data['action'][0] == "mute":
            print "MUTESTATUS : %d" % MyRequestHandler.mute
            if MyRequestHandler.mute == 1:
                MyRequestHandler.mute = 0
                MyRequestHandler.mixer.setmute(MyRequestHandler.mute)
            else:
                MyRequestHandler.mute = 1
                MyRequestHandler.mixer.setmute(MyRequestHandler.mute)
        elif post_data['action'][0] == "volup":
            if MyRequestHandler.volume <= 95:
                MyRequestHandler.volume = MyRequestHandler.volume + 5
                MyRequestHandler.mixer.setvolume(MyRequestHandler.volume)
        elif post_data['action'][0] == "voldown":
            if MyRequestHandler.volume >= 5:
                MyRequestHandler.volume = MyRequestHandler.volume - 5
                MyRequestHandler.mixer.setvolume(MyRequestHandler.volume)


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
                }\
                else if (this.name == "queue")\
                {\
                    $.post( "/", { action: "queue", title: this.id } );\
                }\
                else if (this.name == "stop")\
                {\
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
                \
                });\
            })</script>')
        f.write("<title>Directory listing for %s</title>\n" % self.path)
        f.write('<div class="container">')
        f.write('<div class="row">')
        f.write('<div class="col-xs-12">')
        f.write('<div class="panel panel-default">')
        f.write('<div class="panel-heading"><span class="label label-default">%s</span></div>\n' % (self.path))
        f.write('<div class="panel-body"><span class="badge">%s</span><div class="btn-group pull-right"><button type="button" name="stop" class="btn btn-default btn-sm"><span class="glyphicon glyphicon-stop"></span></button><button type="button" name="volup" class="btn btn-default btn-sm"><span class="glyphicon glyphicon-volume-up"><button type="button" name="voldown" class="btn btn-default btn-sm"><span class="glyphicon glyphicon-volume-down"><button type="button" name="mute" class="btn btn-default btn-sm"><span class="glyphicon glyphicon-volume-off"></span></button></div></div>' % (self.playing))
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
                    if os.path.splitext(name)[-1].lower() in ('.mp3', '.mp4'):
                        if parsed_path.query:
                            f.write('<li class="list-group-item"><span>%s</span><i class="glyphicon glyphicon-time></a><button type="button" id="mama" class="btn btn-default btn-xs pull-right">enqueue</button></li>\n' % (self.path, displayname))
                        else:
                            #f.write('<a href="%s?play=%s" class="list-group-item">%s <span class="glyphicon glyphicon-time"></span></a><button type="button" class="btn btn-default btn-xs pull-right">enqueue</button>\n' % (self.path, fullname, displayname))
                            f.write('<li class="list-group-item">%s<div class="btn-group pull-right"><button type="button" name="play" id="%s" class="btn btn-default btn-sm"><span class="glyphicon glyphicon-play"></span></button><button type="button" name="queue" id="%s" class="btn btn-default btn-sm queue"><span class="glyphicon glyphicon-time"></span></button></div></li>\n' % (displayname, fullname, fullname))
        f.write("</ul>\n<hr>\n")
        f.write("</div>\n")
        f.write("</div>\n")
        f.write("</div>\n")
        f.write("</div>\n")
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        return f

    def startProcess(self, name, path):
        pathname, filename = os.path.split(path)
        MyRequestHandler.playing = filename
        print "STARTPATH : " + path


        """
        Starts a process in the background and writes a PID file

        returns integer: pid
        """
        os.system('pkill omxplayer.bin')
        os.system('pkill mpg123')

        ext = os.path.splitext(path)[-1].lower()
        if ext in ('.mp3', '.wav'):
            print "mpg123 " + path
            process = subprocess.Popen(['/usr/bin/mpg123' , '-q', path] , shell=False)
        elif ext in ('.mp4', ):
            print "omxplayer " + path
            process = subprocess.Popen(['/usr/bin/omxplayer' , path] , shell=False)

        return 1

    def stopAllPlayers(self):
        os.system('pkill omxplayer.bin')
        os.system('pkill mpg123')




server = HTTPServer(("0.0.0.0", 8000), MyRequestHandler)
server.serve_forever()
