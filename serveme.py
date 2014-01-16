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

class MyRequestHandler(SimpleHTTPRequestHandler):

    playing = 0
    def do_GET(self):
        """Serve a GET request."""
        parsed_path = urlparse.urlparse(self.path)
        print parsed_path.query
        if parsed_path.query:
            filetoplay = urlparse.parse_qs(parsed_path.query)['play']
            self.startProcess(self,filetoplay[0])
        f = self.send_head()
        if f:
            self.copyfile(f, self.wfile)
            print "Jippieee FFFFFFFF"
            if (type(f) == type('')):
                print "Juuhuuuuu STRING"
                if os.path.isfile(f):
                    #print "FILE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
                    #self.startProcess(f)
                    test = True
                elif os.path.isdir(f):
                    self.copyfile(f, self.wfile)
            #else:
            #    self.copyfile(f, self.wfile)
            #if os.path.isfile(f.getvalue()):
            #    print "file"
            #    self.startProcess(f.getvalue())
            #print f.getvalue()

            	




    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        print self.path
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            #print "Path : " + path
            return self.list_directory(path)
        if os.path.isfile(path):
            head, tail = os.path.split(self.path)
            #print "head: " + head
            #print "tail: " + tail
            self.startProcess(path)
            path = head
            self.send_response(301)
            self.send_header('Location', head + "/")
            self.end_headers()
        return path

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
        f.write('<script src="//netdna.bootstrapcdn.com/bootstrap/3.0.3/js/bootstrap.min.js"></script>')
        f.write("<title>Directory listing for %s</title>\n" % self.path)
        f.write('<div class="panel panel-default">')
        f.write('<div class="panel-heading"><span class="label label-default">%s</span></div>\n' % (self.path))
        f.write('<div class="panel-body"><span class="badge">%s</span></div>' % (self.playing))
        f.write('<ul class="list-group">\n')
        currentpath = urlparse.urlparse(self.path).path
        #print "CURRENTPATH : " + currentpath
        currentpath = re.sub("/$", "", currentpath)
        dirup, removed = os.path.split(currentpath)
        #print "DIRUP : " + dirup + " REMOVED : " + removed
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
                            f.write('<a href="%s" class="list-group-item">%s<i class="glyphicon glyphicon-time></a>\n' % (self.path, displayname))
                        else:
                            f.write('<a href="%s?play=%s" class="list-group-item">%s <span class="glyphicon glyphicon-time"></span></a>\n' % (self.path, fullname, displayname))
        f.write("</ul>\n<hr>\n")
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

    




server = HTTPServer(("0.0.0.0", 8000), MyRequestHandler)

server.serve_forever()
