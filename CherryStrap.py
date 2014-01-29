import os, sys, time, cherrypy, threading, locale
from lib.configobj import ConfigObj

import cherrystrap
from cherrystrap import webStart, logger

def main():

    # rename this thread
    threading.currentThread().name = "MAIN"

    # Set paths
    if hasattr(sys, 'frozen'):
        cherrystrap.FULL_PATH = os.path.abspath(sys.executable)
    else:
        cherrystrap.FULL_PATH = os.path.abspath(__file__)

    cherrystrap.PROG_DIR = os.path.dirname(cherrystrap.FULL_PATH)
    cherrystrap.ARGS = sys.argv[1:]

    cherrystrap.SYS_ENCODING = None

    try:
        locale.setlocale(locale.LC_ALL, "")
        cherrystrap.SYS_ENCODING = locale.getpreferredencoding()
    except (locale.Error, IOError):
        pass

    # for OSes that are poorly configured I'll just force UTF-8
    if not cherrystrap.SYS_ENCODING or cherrystrap.SYS_ENCODING in ('ANSI_X3.4-1968', 'US-ASCII', 'ASCII'):
        cherrystrap.SYS_ENCODING = 'UTF-8'

    # Set arguments
    from optparse import OptionParser

    p = OptionParser()
    p.add_option('-d', '--daemon', action = "store_true",
                 dest = 'daemon', help = "Run the server as a daemon")
    p.add_option('-q', '--quiet', action = "store_true",
                 dest = 'quiet', help = "Don't log to console")
    p.add_option('--debug', action="store_true",
                 dest = 'debug', help = "Show debuglog messages")
    p.add_option('--nolaunch', action = "store_true",
                 dest = 'nolaunch', help="Don't start browser")
    p.add_option('--port',
                 dest = 'port', default = None,
                 help = "Force webinterface to listen on this port")
    p.add_option('--datadir',
                 dest = 'datadir', default = None,
                 help = "Path to the data directory")
    p.add_option('--config',
                 dest = 'config', default = None,
                 help = "Path to config.ini file")
    p.add_option('-p', '--pidfile',
                 dest = 'pidfile', default = None,
                 help = "Store the process id in the given file")

    options, args = p.parse_args()

    if options.debug:
        cherrystrap.LOGLEVEL = 2

    if options.quiet:
        cherrystrap.LOGLEVEL = 0

    if options.daemon:
        if not sys.platform == 'win32':
            cherrystrap.DAEMON = True
            cherrystrap.LOGLEVEL = 0
            cherrystrap.daemonize()
        else:
            print "Daemonize not supported under Windows, starting normally"

    if options.nolaunch:
        cherrystrap.LAUNCH_BROWSER = False

    if options.datadir:
        cherrystrap.DATADIR = str(options.datadir)
    else:
        cherrystrap.DATADIR = cherrystrap.PROG_DIR

    if options.config:
        cherrystrap.CONFIGFILE = str(options.config)
    else:
        cherrystrap.CONFIGFILE = os.path.join(cherrystrap.DATADIR, "config.ini")

    if options.pidfile:
        if cherrystrap.DAEMON:
            cherrystrap.PIDFILE = str(options.pidfile)

    # create and check (optional) paths
    if not os.path.exists(cherrystrap.DATADIR):
        try:
            os.makedirs(cherrystrap.DATADIR)
        except OSError:
            raise SystemExit('Could not create data directory: ' + cherrystrap.DATADIR + '. Exit ...')

    if not os.access(cherrystrap.DATADIR, os.W_OK):
        raise SystemExit('Cannot write to the data directory: ' + cherrystrap.DATADIR + '. Exit ...')

    # create database and config
    cherrystrap.DBFILE = os.path.join(cherrystrap.DATADIR, 'sqlite.db')
    cherrystrap.CFG = ConfigObj(cherrystrap.CONFIGFILE, encoding='utf-8')

    cherrystrap.initialize()

    if options.port:
        HTTP_PORT = int(options.port)
        logger.info('Starting cherrystrap on forced port: %s' % HTTP_PORT)
    else:
        HTTP_PORT = int(cherrystrap.HTTP_PORT)
        logger.info('Starting cherrystrap on port: %s' % cherrystrap.HTTP_PORT)

    if cherrystrap.DAEMON:
        cherrystrap.daemonize()

    # Try to start the server. 
    webStart.initialize({
                    'http_port': HTTP_PORT,
                    'http_host': cherrystrap.HTTP_HOST,
                    'http_root': cherrystrap.HTTP_ROOT,
                    'http_user': cherrystrap.HTTP_USER,
                    'http_pass': cherrystrap.HTTP_PASS,
            })

    if cherrystrap.LAUNCH_BROWSER and not options.nolaunch:
        cherrystrap.launch_browser(cherrystrap.HTTP_HOST, cherrystrap.HTTP_PORT, cherrystrap.HTTP_ROOT)

    cherrystrap.start()

    while True:
        if not cherrystrap.SIGNAL:

            try:
                time.sleep(1)
            except KeyboardInterrupt:
                cherrystrap.shutdown()
        else:
            if cherrystrap.SIGNAL == 'shutdown':
                cherrystrap.shutdown()
            elif cherrystrap.SIGNAL == 'restart':
                cherrystrap.shutdown(restart=True)
            else:
                cherrystrap.shutdown(restart=True, update=True)
            cherrystrap.SIGNAL = None
    return

if __name__ == "__main__":
    main()
