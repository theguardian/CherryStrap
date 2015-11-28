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

FULL_PATH = None
PROG_DIR = None

ARGS = None
SIGNAL = None

LOGLEVEL = 1
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

LOGIN_STATUS=False

LOGDIR = None
LOGLIST = []

APP_NAME = 'CherryStrap'
HTTP_ROOT = None
HTTP_HOST = None
HTTP_PORT = None
HTTPS_ENABLED = False
HTTPS_KEY = 'keys/server.key'
HTTPS_CERT = 'keys/server.crt'
VERIFY_SSL = True
LAUNCH_BROWSER = False

HTTP_USER = None
HTTP_PASS = None
HTTP_LOOK = None
API_TOKEN = None

DATABASE_TYPE = 'sqlite'
MYSQL_HOST = None
MYSQL_PORT = None
MYSQL_USER = None
MYSQL_PASS = None

GIT_ENABLE = True
GIT_PATH = None
GIT_USER = 'theguardian'
GIT_REPO = 'CherryStrap'
GIT_BRANCH = 'master'
GIT_UPSTREAM = None
GIT_LOCAL = None
GIT_STARTUP = True
GIT_INTERVAL = 6
GIT_OVERRIDE = False

def CheckSection(sec):
    """ Check if INI section exists, if not create it """
    try:
        CFG[sec]
        return True
    except:
        CFG[sec] = {}
        return False

################################################################################
# Check_setting_int                                                            #
################################################################################
def check_setting_int(config, cfg_name, item_name, def_val):
    try:
        my_val = int(config[cfg_name][item_name])
    except:
        my_val = def_val
        try:
            config[cfg_name][item_name] = my_val
        except:
            config[cfg_name] = {}
            config[cfg_name][item_name] = my_val
    logger.debug(item_name + " -> " + str(my_val))
    return my_val

################################################################################
# Check_setting_str                                                            #
################################################################################
def check_setting_str(config, cfg_name, item_name, def_val, log=True):
    try:
        my_val = config[cfg_name][item_name]
    except:
        my_val = def_val
        try:
            config[cfg_name][item_name] = my_val
        except:
            config[cfg_name] = {}
            config[cfg_name][item_name] = my_val

    if log:
        logger.debug(item_name + " -> " + my_val)
    else:
        logger.debug(item_name + " -> ******")

    return my_val

def initialize():

    with INIT_LOCK:

        global __INITIALIZED__, FULL_PATH, PROG_DIR, LOGLEVEL, DAEMON, \
        DATADIR, CONFIGFILE, CFG, LOGDIR, APP_NAME, HTTP_HOST, HTTP_PORT, \
        HTTP_USER, HTTP_PASS, HTTP_ROOT, HTTP_LOOK, VERIFY_SSL, \
        LAUNCH_BROWSER, HTTPS_ENABLED, HTTPS_KEY, HTTPS_CERT, API_TOKEN, \
        DATABASE_TYPE, MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASS, \
        GIT_ENABLE, GIT_PATH, GIT_BRANCH, GIT_USER, GIT_STARTUP, GIT_INTERVAL, \
        GIT_OVERRIDE, GIT_REPO, GIT_UPSTREAM, GIT_LOCAL

        if __INITIALIZED__:
            return False

        CheckSection('Server')
        CheckSection('Interface')
        CheckSection('Database')
        CheckSection('Git')

        try:
            HTTP_PORT = check_setting_int(CFG, 'Server', 'http_port', 7889)
        except:
            HTTP_PORT = 7889

        if HTTP_PORT < 21 or HTTP_PORT > 65535:
            HTTP_PORT = 7889

        APP_NAME = check_setting_str(CFG, 'Server', 'app_name', 'CherryStrap')
        HTTP_ROOT = check_setting_str(CFG, 'Server', 'http_root', '')
        LOGDIR = check_setting_str(CFG, 'Server', 'logdir', '')
        HTTP_HOST = check_setting_str(CFG, 'Server', 'http_host', '0.0.0.0')
        HTTPS_ENABLED = bool(check_setting_int(CFG, 'Server', 'https_enabled', 0))
        HTTPS_KEY = check_setting_str(CFG, 'Server', 'https_key', 'keys/server.key')
        HTTPS_CERT = check_setting_str(CFG, 'Server', 'https_cert', 'keys/server.crt')
        VERIFY_SSL = bool(check_setting_int(CFG, 'Server', 'verify_ssl', 1))
        LAUNCH_BROWSER = bool(check_setting_int(CFG, 'Server', 'launch_browser', 0))

        HTTP_USER = check_setting_str(CFG, 'Interface', 'http_user', '')
        HTTP_PASS = check_setting_str(CFG, 'Interface', 'http_pass', '')
        HTTP_LOOK = check_setting_str(CFG, 'Interface', 'http_look', 'bootstrap')
        API_TOKEN = check_setting_str(CFG, 'Interface', 'api_token', uuid.uuid4().hex)

        DATABASE_TYPE = check_setting_str(CFG, 'Database', 'database_type', 'sqlite')
        MYSQL_HOST = check_setting_str(CFG, 'Database', 'mysql_host', 'localhost')
        MYSQL_PORT = check_setting_int(CFG, 'Database', 'mysql_port', 3306)
        MYSQL_USER = check_setting_str(CFG, 'Database', 'mysql_user', '')
        MYSQL_PASS = check_setting_str(CFG, 'Database', 'mysql_pass', '')

        GIT_ENABLE = bool(check_setting_int(CFG, 'Git', 'git_enable', 1))
        GIT_PATH = check_setting_str(CFG, 'Git', 'git_path', '/usr/bin/git')
        GIT_USER = check_setting_str(CFG, 'Git', 'git_user', 'theguardian')
        GIT_REPO = check_setting_str(CFG, 'Git', 'git_repo', 'CherryStrap')
        GIT_BRANCH = check_setting_str(CFG, 'Git', 'git_branch', 'master')
        GIT_UPSTREAM = check_setting_str(CFG, 'Git', 'git_upstream', '')
        GIT_LOCAL = check_setting_str(CFG, 'Git', 'git_local', '')
        GIT_STARTUP = bool(check_setting_int(CFG, 'Git', 'git_startup', 1))
        GIT_INTERVAL = check_setting_int(CFG, 'Git', 'git_interval', 6)
        GIT_OVERRIDE = bool(check_setting_int(CFG, 'Git', 'git_override', 0))

        if not LOGDIR:
            LOGDIR = os.path.join(DATADIR, 'Logs')

        # Put the cache dir in the data dir for now
        CACHEDIR = os.path.join(DATADIR, 'cache')
        if not os.path.exists(CACHEDIR):
            try:
                os.makedirs(CACHEDIR)
            except OSError:
                logger.error('Could not create cachedir. Check permissions of: ' + DATADIR)

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

        # Initialize the database
        try:
            dbcheck()
        except Exception, e:
            logger.error("Can't connect to the database: %s" % e)

        # Get the currently installed version. Returns None, 'win32' or the git
        # hash.
        GIT_LOCAL, GIT_BRANCH = versioncheck.getVersion()

        # Write current version to a file, so we know which version did work.
        # This allowes one to restore to that version. The idea is that if we
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
        if GIT_ENABLE and GIT_STARTUP:
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
    new_config['Server']['app_name'] = APP_NAME
    new_config['Server']['http_root'] = HTTP_ROOT
    new_config['Server']['logdir'] = LOGDIR
    new_config['Server']['http_host'] = HTTP_HOST
    new_config['Server']['http_port'] = HTTP_PORT
    new_config['Server']['https_enabled'] = int(HTTPS_ENABLED)
    new_config['Server']['https_key'] = HTTPS_KEY
    new_config['Server']['https_cert'] = HTTPS_CERT
    new_config['Server']['verify_ssl'] = int(VERIFY_SSL)
    new_config['Server']['launch_browser'] = int(LAUNCH_BROWSER)

    new_config['Interface'] = {}
    new_config['Interface']['http_user'] = HTTP_USER
    new_config['Interface']['http_pass'] = HTTP_PASS
    new_config['Interface']['http_look'] = HTTP_LOOK
    new_config['Interface']['api_token'] = API_TOKEN

    new_config['Database'] = {}
    new_config['Database']['database_type'] = DATABASE_TYPE
    new_config['Database']['mysql_host'] = MYSQL_HOST
    new_config['Database']['mysql_port'] = MYSQL_PORT
    new_config['Database']['mysql_user'] = MYSQL_USER
    new_config['Database']['mysql_pass'] = MYSQL_PASS

    new_config['Git'] = {}
    new_config['Git']['git_enable'] = int(GIT_ENABLE)
    new_config['Git']['git_path'] = GIT_PATH
    new_config['Git']['git_user'] = GIT_USER
    new_config['Git']['git_repo'] = GIT_REPO
    new_config['Git']['git_branch'] = GIT_BRANCH
    new_config['Git']['git_upstream'] = GIT_UPSTREAM
    new_config['Git']['git_local'] = GIT_LOCAL
    new_config['Git']['git_startup'] = int(GIT_STARTUP)
    new_config['Git']['git_interval'] = GIT_INTERVAL
    new_config['Git']['git_override'] = int(GIT_OVERRIDE)

    new_config.write()

def dbcheck():

    # User should have a choice between sqlite and mysql

    if DATABASE_TYPE == "sqlite":
        try:
            import sqlite3
        except Exception, e:
            logger.warn("SQLite is not installed: %s" % e)
        conn = sqlite3.connect(DBFILE)
        c = conn.cursor()
        # Create and modify your database here

        # c.execute('CREATE TABLE IF NOT EXISTS authors (AuthorID TEXT, AuthorName TEXT UNIQUE)')
        # try:
        #     c.execute('SELECT UnignoredBooks from authors')
        #     logger.info('Updating database to hold UnignoredBooks')
        # except sqlite3.OperationalError:
        #     logger.error('Could not create column Unignored Books in table authors')
        #     c.execute('ALTER TABLE authors ADD COLUMN UnignoredBooks INTEGER')

        conn.commit()
        c.close()
    elif DATABASE_TYPE == "mysql":
        try:
            import MySQLdb
        except Exception, e:
            logger.warn("MySQLdb is not installed: %s" % e)
        # Uncomment this if you have mysql configured and want to create a db
        # try:
        #     conn_ini = MySQLdb.Connection(host=MYSQL_HOST, port=MYSQL_PORT,
        #     user=MYSQL_USER, passwd=formatter.decode('obscure', MYSQL_PASS),
        #     charset='utf8', use_unicode=True)
        #     c_ini = conn_ini.cursor(MySQLdb.cursors.DictCursor)
        #     c_ini.execute('CREATE DATABASE IF NOT EXISTS %s' % APP_NAME)
        #     conn_ini.commit()
        #     c_ini.close()
        # except Exception, e:
        #     logger.warn("There was a problem creating the MySQL database: %s" % e)

        # Now we're free to build our schema

        try:
            conn = MySQLdb.Connection(host=MYSQL_HOST, port=MYSQL_PORT,
            user=MYSQL_USER, passwd=formatter.decode('obscure', MYSQL_PASS),
            charset='utf8', use_unicode=True, db=APP_NAME)
            c = conn.cursor(MySQLdb.cursors.DictCursor)
            # table creation and augment statements go here
            #c.execute('CREATE TABLE IF NOT EXISTS authors (AuthorID VARCHAR(30) PRIMARY KEY, AuthorName TEXT)')
            conn.commit()
            c.close()
        except Exception, e:
            logger.warn("There was a problem initializing the MySQL database: %s" % e)

def start():
    global __INITIALIZED__, scheduler_started

    if __INITIALIZED__:

        #Update check
        if GIT_ENABLE:
            if GIT_INTERVAL:
                gitHours = GIT_INTERVAL
            else:
                gitHours = 0

        try:
            # Crons and scheduled jobs go here
            # testInterval = IntervalTrigger(weeks=0, days=0, hours=0, minutes=2, seconds=0, start_date=None, end_date=None, timezone=None)
            # testCron = CronTrigger(year=None, month=None, day=None, week=None, day_of_week=None, hour=None, minute='*/2', second=None, start_date=None, end_date=None, timezone=None)
            # SCHED.add_job(formatter.schedulerTest, testCron)
            if gitHours != 0:
                gitInterval = IntervalTrigger(weeks=0, days=0, hours=gitHours, minutes=0, seconds=0, start_date=None, end_date=None, timezone=None)
                SCHED.add_job(versioncheck.checkGithub, gitInterval)
            SCHED.start()
            scheduler_started = True
        except Exception, e:
            logger.error("Can't start scheduled job(s): %s" % e)

def shutdown(restart=False):
    config_write()
    logger.info('%s is shutting down ...' % APP_NAME)
    cherrypy.engine.exit()

    try:
        SCHED.shutdown(wait=True)
    except Exception, e:
        logger.error("Can't shutdown scheduler: %s" % e)

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
