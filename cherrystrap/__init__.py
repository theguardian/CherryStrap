"""
This file deals primarily with initializing, writing, and connecting
to services needed by the web application at runtime
(e.g. sqlite3, apscheduler, config.ini file) and also contains
runtime commands like daemonizing, restarting, and shutting down the web app.
"""

from __future__ import with_statement

import os, sys, subprocess, threading, cherrypy, datetime, uuid

from lib.configobj.configobj import ConfigObj
from lib.apscheduler.schedulers.background import BackgroundScheduler
from lib.apscheduler.triggers.interval import IntervalTrigger
from lib.apscheduler.triggers.cron import CronTrigger
from cherrystrap import logger, formatter, versioncheck
from configCheck import CheckSection, check_setting_int, check_setting_bool, check_setting_str
from initializeDb import createDb

FULL_PATH = None
PROG_DIR = None

ARGS = None
SIGNAL = None

LOGLEVEL = 2
DAEMON = False
PIDFILE = None

SYS_ENCODING = None

SCHED = BackgroundScheduler()

INIT_LOCK = threading.Lock()
__INITIALIZED__ = False

DATADIR = None
DBFILE = None
CONFIGFILE = None
CFG = None

LOGIN_STATUS = False
COMMITS_BEHIND = None
IGNORE_UPDATES = False

LOGDIR = None
LOGLIST = []

APP_NAME = None
HTTP_ROOT = None
HTTP_HOST = None
HTTP_PORT = None
HTTPS_ENABLED = False
HTTPS_KEY = None
HTTPS_CERT = None
VERIFY_SSL = True
LAUNCH_BROWSER = False

HTTP_USER = None
HTTP_PASS = None
HTTP_LOOK = None
API_TOKEN = None

DATABASE_TYPE = None
MYSQL_HOST = None
MYSQL_PORT = None
MYSQL_USER = None
MYSQL_PASS = None

GIT_EXISTS = False
GIT_USER = None
GIT_REPO = None
GIT_BRANCH = None
GIT_UPSTREAM = None
GIT_LOCAL = None
GIT_OVERRIDE = False
GIT_ENABLED = False
GIT_PATH = None
GIT_STARTUP = False
GIT_INTERVAL = 0

def initialize():

    with INIT_LOCK:

        global __INITIALIZED__, FULL_PATH, PROG_DIR, LOGLEVEL, DAEMON, \
        DATADIR, CONFIGFILE, CFG, LOGDIR, APP_NAME, HTTP_HOST, HTTP_PORT, \
        HTTP_USER, HTTP_PASS, HTTP_ROOT, HTTP_LOOK, VERIFY_SSL, \
        LAUNCH_BROWSER, HTTPS_ENABLED, HTTPS_KEY, HTTPS_CERT, API_TOKEN, \
        DATABASE_TYPE, MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASS, \
        GIT_ENABLED, GIT_PATH, GIT_BRANCH, GIT_USER, GIT_STARTUP, GIT_INTERVAL, \
        GIT_OVERRIDE, GIT_REPO, GIT_UPSTREAM, GIT_LOCAL, GIT_EXISTS

        if __INITIALIZED__:
            return False

        CheckSection(CFG, 'Server')
        CheckSection(CFG, 'Interface')
        CheckSection(CFG, 'Database')
        CheckSection(CFG, 'Git')

        LOGDIR = check_setting_str(CFG, 'Server', 'logDir', '')

        if not LOGDIR:
            LOGDIR = os.path.join(DATADIR, 'Logs')

        # Create logdir
        if not os.path.exists(LOGDIR):
            try:
                os.makedirs(LOGDIR)
            except OSError:
                if LOGLEVEL:
                    print LOGDIR + ":"
                    print ' Unable to create folder for logs. Only logging to console.'

        # Start the logger, silence console logging if we need to
        logger.cherrystrap_log.initLogger(loglevel=LOGLEVEL)

        # Put the cache dir in the data dir for now
        CACHEDIR = os.path.join(DATADIR, 'cache')
        if not os.path.exists(CACHEDIR):
            try:
                os.makedirs(CACHEDIR)
            except OSError:
                logger.error('Could not create cachedir. Check permissions of: ' + DATADIR)

        GIT_EXISTS = os.path.isdir(os.path.join(DATADIR, '.git'))

        # Attempt to find location of git in this environment
        if GIT_EXISTS:
            output = err = None
            cmd = 'which git'
            try:
                logger.debug('Trying to execute: "' + cmd + '" with shell in ' + os.getcwd())
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, cwd=os.getcwd())
                output, err = p.communicate()
                output = output.strip()
                logger.debug('Git output: ' + output)
            except OSError:
                logger.debug('Command failed: %s', cmd)

            if not output or 'not found' in output or "not recognized as an internal or external command" in output:
                logger.debug('Unable to find git with command ' + cmd)
                git_enabled = False
                git_path = ''
                git_startup = False
                git_interval = 0
            else:
                git_enabled = True
                git_path = output
                git_startup = True
                git_interval = 12
        else:
                git_enabled = False
                git_path = ''
                git_startup = False
                git_interval = 0

        try:
            HTTP_PORT = check_setting_int(CFG, 'Server', 'httpPort', 7889)
        except:
            HTTP_PORT = 7889

        if HTTP_PORT < 21 or HTTP_PORT > 65535:
            HTTP_PORT = 7889

        APP_NAME = check_setting_str(CFG, 'Server', 'appName', 'CherryStrap')
        HTTP_ROOT = check_setting_str(CFG, 'Server', 'httpRoot', '')
        HTTP_HOST = check_setting_str(CFG, 'Server', 'httpHost', '0.0.0.0')
        HTTPS_ENABLED = check_setting_bool(CFG, 'Server', 'sslEnabled', False)
        HTTPS_KEY = check_setting_str(CFG, 'Server', 'sslKey', 'keys/server.key')
        HTTPS_CERT = check_setting_str(CFG, 'Server', 'sslCert', 'keys/server.crt')
        VERIFY_SSL = check_setting_bool(CFG, 'Server', 'sslVerify', True)
        LAUNCH_BROWSER = check_setting_bool(CFG, 'Server', 'launchBrowser', False)

        HTTP_USER = check_setting_str(CFG, 'Interface', 'httpUser', '')
        HTTP_PASS = check_setting_str(CFG, 'Interface', 'httpPass', '')
        HTTP_LOOK = check_setting_str(CFG, 'Interface', 'httpLook', 'bootstrap')
        API_TOKEN = check_setting_str(CFG, 'Interface', 'apiToken', uuid.uuid4().hex)

        DATABASE_TYPE = check_setting_str(CFG, 'Database', 'dbType', '')
        MYSQL_HOST = check_setting_str(CFG, 'Database', 'mysqlHost', 'localhost')
        MYSQL_PORT = check_setting_int(CFG, 'Database', 'mysqlPort', 3306)
        MYSQL_USER = check_setting_str(CFG, 'Database', 'mysqlUser', '')
        MYSQL_PASS = check_setting_str(CFG, 'Database', 'mysqlPass', '')

        GIT_ENABLED = check_setting_bool(CFG, 'Git', 'gitEnabled', git_enabled)
        GIT_PATH = check_setting_str(CFG, 'Git', 'gitPath', git_path)
        GIT_USER = check_setting_str(CFG, 'Git', 'gitUser', 'theguardian')
        GIT_REPO = check_setting_str(CFG, 'Git', 'gitRepo', 'CherryStrap')
        GIT_BRANCH = check_setting_str(CFG, 'Git', 'gitBranch', 'master')
        GIT_UPSTREAM = check_setting_str(CFG, 'Git', 'gitUpstream', '')
        GIT_LOCAL = check_setting_str(CFG, 'Git', 'gitLocal', '')
        GIT_STARTUP = check_setting_bool(CFG, 'Git', 'gitStartup', git_startup)
        GIT_INTERVAL = check_setting_int(CFG, 'Git', 'gitInterval', git_interval)
        GIT_OVERRIDE = check_setting_bool(CFG, 'Git', 'gitOverride', False)

        #===============================================================
        # Import a variable definer / checker from your app's __init__.py
        try:
            from yourapp import injectVarCheck
            injectVarCheck(CFG)
        except Exception, e:
            logger.debug("There was a problem importing application variable definitions: %s" % e)
        #================================================================


        # Initialize the database
        try:
            createDb(DATABASE_TYPE, DATADIR, APP_NAME, MYSQL_HOST, MYSQL_PORT,
                MYSQL_USER, MYSQL_PASS)
        except Exception, e:
            logger.error("Error initializing the database: %s" % e)

        # Disable SSL verification for systems where SSL is broken
        if not VERIFY_SSL:
            try:
                import ssl
                ssl._create_default_https_context = ssl._create_unverified_context
                logger.info("SSL verification disabled per user preferences")
            except Exception, e:
                logger.warn("There was an error disabling SSL verification: %s" % s)
                pass

        # Get the currently installed version. Returns None, 'win32' or the git
        # hash.
        GIT_LOCAL, GIT_BRANCH = versioncheck.getVersion()

        # Write current version to a file, so we know which version did work.
        # This allows one to restore to that version. The idea is that if we
        # arrive here, most parts of the app seem to work.
        if GIT_LOCAL:
            version_lock_file = os.path.join(DATADIR, "version.lock")

            try:
                with open(version_lock_file, "w") as fp:
                    fp.write(GIT_LOCAL)
            except IOError as e:
                logger.error("Unable to write current version to file '%s': %s",
                             version_lock_file, e)

        # Check for new versions
        if GIT_ENABLED and GIT_STARTUP:
            try:
                GIT_UPSTREAM = versioncheck.checkGithub()
            except:
                logger.error("Unhandled exception in version check")
                GIT_UPSTREAM = GIT_LOCAL
        else:
            GIT_UPSTREAM = GIT_LOCAL

        # Store the original umask
        UMASK = os.umask(0)
        os.umask(UMASK)

        __INITIALIZED__ = True
        return True

def daemonize():
    """
    Fork off as a daemon
    """

    # Make a non-session-leader child process
    try:
        pid = os.fork() #@UndefinedVariable - only available in UNIX
        if pid != 0:
            sys.exit(0)
    except OSError, e:
        raise RuntimeError("1st fork failed: %s [%d]" % (e.strerror, e.errno))

    os.setsid() #@UndefinedVariable - only available in UNIX

    # Make sure I can read my own files and shut out others
    prev = os.umask(0)
    os.umask(prev and int('077', 8))

    # Make the child a session-leader by detaching from the terminal
    try:
        pid = os.fork() #@UndefinedVariable - only available in UNIX
        if pid != 0:
            sys.exit(0)
    except OSError, e:
        raise RuntimeError("2st fork failed: %s [%d]" % (e.strerror, e.errno))

    dev_null = file('/dev/null', 'r')
    os.dup2(dev_null.fileno(), sys.stdin.fileno())

    if PIDFILE:
        pid = str(os.getpid())
        logger.debug(u"Writing PID " + pid + " to " + str(PIDFILE))
        file(PIDFILE, 'w').write("%s\n" % pid)

def launch_browser(host, port, root):
    if host == '0.0.0.0':
        host = 'localhost'

    if HTTPS_ENABLED:
        protocol = 'https'
    else:
        protocol = 'http'

    try:
        import webbrowser
        webbrowser.open('%s://%s:%i%s' % (protocol, host, port, root))
    except Exception, e:
        logger.error('Could not launch browser: %s' % e)

def config_write():
    new_config = ConfigObj()
    new_config.filename = CONFIGFILE

    new_config['Server'] = {}
    new_config['Server']['appName'] = APP_NAME
    new_config['Server']['httpRoot'] = HTTP_ROOT
    new_config['Server']['logDir'] = LOGDIR
    new_config['Server']['httpHost'] = HTTP_HOST
    new_config['Server']['httpPort'] = HTTP_PORT
    new_config['Server']['sslEnabled'] = HTTPS_ENABLED
    new_config['Server']['sslKey'] = HTTPS_KEY
    new_config['Server']['sslCert'] = HTTPS_CERT
    new_config['Server']['sslVerify'] = VERIFY_SSL
    new_config['Server']['launchBrowser'] = LAUNCH_BROWSER

    new_config['Interface'] = {}
    new_config['Interface']['httpUser'] = HTTP_USER
    new_config['Interface']['httpPass'] = HTTP_PASS
    new_config['Interface']['httpLook'] = HTTP_LOOK
    new_config['Interface']['apiToken'] = API_TOKEN

    new_config['Database'] = {}
    new_config['Database']['dbType'] = DATABASE_TYPE
    new_config['Database']['mysqlHost'] = MYSQL_HOST
    new_config['Database']['mysqlPort'] = MYSQL_PORT
    new_config['Database']['mysqlUser'] = MYSQL_USER
    new_config['Database']['mysqlPass'] = MYSQL_PASS

    new_config['Git'] = {}
    new_config['Git']['gitEnabled'] = GIT_ENABLED
    new_config['Git']['gitPath'] = GIT_PATH
    new_config['Git']['gitUser'] = GIT_USER
    new_config['Git']['gitRepo'] = GIT_REPO
    new_config['Git']['gitBranch'] = GIT_BRANCH
    new_config['Git']['gitUpstream'] = GIT_UPSTREAM
    new_config['Git']['gitLocal'] = GIT_LOCAL
    new_config['Git']['gitStartup'] = GIT_STARTUP
    new_config['Git']['gitInterval'] = GIT_INTERVAL
    new_config['Git']['gitOverride'] = GIT_OVERRIDE

    #===============================================================
    # Import a variable writer from your app's __init__.py
    try:
        from yourapp import injectVarWrite
        injectVarWrite(new_config)
    except Exception, e:
        logger.debug("There was a problem importing application variables to write: %s" % e)
    #================================================================

    new_config.write()

def start():
    global __INITIALIZED__, scheduler_started

    if __INITIALIZED__:

        try:
            # Crons and scheduled jobs go here
            # testInterval = IntervalTrigger(weeks=0, days=0, hours=0, minutes=2, seconds=0, start_date=None, end_date=None, timezone=None)
            # testCron = CronTrigger(year=None, month=None, day=None, week=None, day_of_week=None, hour=None, minute='*/2', second=None, start_date=None, end_date=None, timezone=None)
            # SCHED.add_job(formatter.schedulerTest, testCron)
            if GIT_ENABLED and GIT_INTERVAL != 0:
                gitInterval = IntervalTrigger(weeks=0, days=0, hours=GIT_INTERVAL, minutes=0, seconds=0, start_date=None, end_date=None, timezone=None)
                SCHED.add_job(versioncheck.checkGithub, gitInterval)
            SCHED.start()
            for job in SCHED.get_jobs():
                logger.info("Job scheduled: %s" % job)
            scheduler_started = True
        except Exception, e:
            logger.error("Can't start scheduled job(s): %s" % e)

def shutdown(restart=False, update=False):
    config_write()
    cherrypy.engine.exit()

    try:
        SCHED.shutdown(wait=True)
    except Exception, e:
        logger.error("Can't shutdown scheduler: %s" % e)

    if not restart and not update:
        logger.info('%s is shutting down ...' % APP_NAME)

    if update:
        logger.info('%s is updating ...' % APP_NAME)
        try:
            versioncheck.update()
        except Exception as e:
            logger.warn('%s failed to update: %s. Restarting ...' % (APP_NAME, e))

    if PIDFILE:
        logger.info('Removing pidfile %s' % PIDFILE)
        os.remove(PIDFILE)

    if restart:
        logger.info('%s is restarting ...' % APP_NAME)
        popen_list = [sys.executable, FULL_PATH]
        popen_list += ARGS
        if '--nolaunch' not in popen_list:
            popen_list += ['--nolaunch']
            prepend_msg = 'Restarting ' + APP_NAME + ' with '
            logger.info(prepend_msg + str(popen_list))
        subprocess.Popen(popen_list, cwd=os.getcwd())

    os._exit(0)
