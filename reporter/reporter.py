import logging
import urllib2
import os
import time
import optparse
from flask import Flask, url_for, render_template, abort, Response
from xml.dom.minidom import parse

LOGGER = logging.getLogger('osm-reporter')
app = Flask(__name__)



@app.route('/')
def hello_world():
    myUrlPath = ('http://www.openstreetmap.org/api/0.6/'
                 'map?bbox=20.411482,-34.053726,20.467358,-34.009483')
    myFilePath = '/tmp/swellendam.osm'
    myElapsedSeconds = 0
    if os.path.exists(myFilePath):
        myTime = time.time()  # in unix epoch
        myFileTime = os.path.getmtime(myFilePath)  # in unix epoch
        myElapsedSeconds = myTime - myFileTime
        if myElapsedSeconds > 3600:
            os.remove(myFilePath)

    if myElapsedSeconds > 3600 or not os.path.exists(myFilePath):
        fetch_osm(myUrlPath, myFilePath)
        LOGGER.info('fetched %s' % myFilePath)

    myFile = open(myFilePath, 'rt')
    myDom = parse(myFile)
    myFile.close()

    myUserDict = {}
    myWays = myDom.getElementsByTagName('way')
    for myWay in myWays:
        if myWay.hasAttribute('user'):
            myUser = myWay.attributes['user'].value
            if myUser in myUserDict:
                myValue = myUserDict[myUser]
                myUserDict[myUser] = myValue + 1
            else:
                myUserDict[myUser] = 1

    myReport = ''
    for myUserName, myUserScore in myUserDict.iteritems():
        myReport += '%s : %i<br/>' % (myUserName, myUserScore)

    return render_template('base.html', myUserDict=myUserDict)

def fetch_osm(theUrlPath, theFilePath):
    """Fetch an osm map and store locally.

     Args:
        * theUrlPath - (Mandatory) The path (relative to the ftp root)
          from which the file should be retrieved.
        * theFilePath - (Mandatory). The path on the filesystem to which
          the file should be saved.
     Returns:
         The path to the downloaded file.

     Raises:
         None
    """
    LOGGER.debug('Getting URL: %s', theUrlPath)
    myRequest = urllib2.Request(theUrlPath)
    try:
        myUrlHandle = urllib2.urlopen(myRequest, timeout=60)
        myFile = file(theFilePath, 'wb')
        myFile.write(myUrlHandle.read())
        myFile.close()
    except urllib2.URLError, e:
        LOGGER.exception('Bad Url or Timeout')
        raise


#
# These are only used to serve static files when testing
#
file_suffix_to_mimetype = {
    '.css': 'text/css',
    '.jpg': 'image/jpeg',
    '.html': 'text/html',
    '.ico': 'image/x-icon',
    '.png': 'image/png',
    '.js': 'application/javascript'
}


def static_file(path):
    try:
        f = open(path)
    except IOError, e:
        abort(404)
        return
    root, ext = os.path.splitext(path)
    if ext in file_suffix_to_mimetype:
        return Response(f.read(), mimetype=file_suffix_to_mimetype[ext])
    return f.read()


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-d', '--debug', dest='debug', default=False,
                      help='turn on Flask debugging', action='store_true')

    options, args = parser.parse_args()

    if options.debug:
        app.debug = True
        # set up flask to serve static content
        app.add_url_rule('/<path:path>', 'static_file', static_file)
    app.run()
