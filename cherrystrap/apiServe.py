import collections
import cherrypy
import cherrystrap
from cherrypy import _cperror
from lib import simplejson as json
from lib.passlib.hash import sha256_crypt
from cherrystrap import logger, formatter

class settings(object):
    exposed = True

    def GET(self, token=None):

        if token != cherrystrap.API_TOKEN:
            return "{\"error\": \"Invalid Token\"}"

        configuration = {
            "appName":  cherrystrap.APP_NAME,
            "logDir": cherrystrap.LOGDIR,
            "httpHost": cherrystrap.HTTP_HOST,
            "httpPort": cherrystrap.HTTP_PORT,
            "sslEnabled": bool(cherrystrap.HTTPS_ENABLED),
            "sslKey": cherrystrap.HTTPS_KEY,
            "sslCert": cherrystrap.HTTPS_CERT,
            "sslVerify": bool(cherrystrap.VERIFY_SSL),
            "httpUser": cherrystrap.HTTP_USER,
            "httpPass": cherrystrap.HTTP_PASS,
            "httpLook": cherrystrap.HTTP_LOOK,
            "apiToken": cherrystrap.API_TOKEN,
            "launchBrowser": bool(cherrystrap.LAUNCH_BROWSER),
            "dbType": cherrystrap.DATABASE_TYPE,
            "mysqlHost": cherrystrap.MYSQL_HOST,
            "mysqlPort": cherrystrap.MYSQL_PORT,
            "mysqlUser": cherrystrap.MYSQL_USER,
            "mysqlPass": cherrystrap.MYSQL_PASS,
            "gitEnabled": bool(cherrystrap.GIT_ENABLED),
            "gitPath": cherrystrap.GIT_PATH,
            "gitUser": cherrystrap.GIT_USER,
            "gitRepo": cherrystrap.GIT_REPO,
            "gitBranch": cherrystrap.GIT_BRANCH,
            "gitUpstream": cherrystrap.GIT_UPSTREAM,
            "gitLocal": cherrystrap.GIT_LOCAL,
            "gitStartup": bool(cherrystrap.GIT_STARTUP),
            "gitInterval": cherrystrap.GIT_INTERVAL,
            "gitOverride": bool(cherrystrap.GIT_OVERRIDE)
        }
        config = json.dumps(configuration)
        return config

    def POST(self, token=None):
        if token != cherrystrap.API_TOKEN:
            return "{\"error\": \"Invalid Token\"}"
        return "{\"error\": \"PUT not available at this endpoint\"}"

    def PUT(self, token=None, **kwargs):

        if token != cherrystrap.API_TOKEN:
            return "{\"error\": \"Invalid Token\"}"

        cherrystrap.APP_NAME = kwargs.pop('"app_name', 'CherryStrap')
        cherrystrap.LOGDIR = kwargs.pop('logdir', None)
        cherrystrap.HTTP_HOST = kwargs.pop('http_host', '0.0.0.0')
        cherrystrap.HTTP_PORT = kwargs.pop('http_port', 7889)
        cherrystrap.HTTPS_ENABLED = kwargs.pop('https_enabled', False) == 'on'
        cherrystrap.HTTPS_KEY = kwargs.pop('https_key', 'keys/server.key')
        cherrystrap.HTTPS_CERT = kwargs.pop('https_cert', 'keys/server.crt')
        cherrystrap.VERIFY_SSL = kwargs.pop('verify_ssl', True) == 'on'
        cherrystrap.LAUNCH_BROWSER = kwargs.pop('launch_browser', False) == 'on'
        cherrystrap.HTTP_USER = kwargs.pop('http_user', None)
        httpPassProcess = kwargs.pop('http_pass', None)
        if httpPassProcess != cherrystrap.HTTP_PASS and httpPassProcess != "":
            try:
                cherrystrap.HTTP_PASS = sha256_crypt.encrypt(httpPassProcess)
            except Exception, e:
                logger.error('There was a problem generating password hash: %s' % e)
        elif httpPassProcess == "":
            cherrystrap.HTTP_PASS = ""
        cherrystrap.HTTP_LOOK = kwargs.pop('http_look', 'bootstrap')
        cherrystrap.API_TOKEN = kwargs.pop('api_token', None)
        cherrystrap.DATABASE_TYPE = kwargs.pop('database_type', 'sqlite')
        cherrystrap.MYSQL_HOST = kwargs.pop('mysql_host', 'localhost')
        cherrystrap.MYSQL_PORT = kwargs.pop('mysql_port', 3306)
        cherrystrap.MYSQL_USER = kwargs.pop('mysql_user', None)
        mysqlPassProcess = kwargs.pop('mysql_pass', None)
        if mysqlPassProcess != cherrystrap.MYSQL_PASS and mysqlPassProcess != "":
            try:
                cherrystrap.MYSQL_PASS = formatter.encode('obscure', mysqlPassProcess)
            except Exception, e:
                logger.error('There was a problem encoding MySQL password: %s' % e)
        elif mysqlPassProcess == "":
            cherrystrap.MYSQL_PASS = ""
        cherrystrap.GIT_ENABLED = kwargs.pop('git_enabled', False) == 'on'
        cherrystrap.GIT_PATH = kwargs.pop('git_path', None)
        cherrystrap.GIT_USER = kwargs.pop('git_user', 'theguardian')
        cherrystrap.GIT_REPO = kwargs.pop('git_repo', 'CherryStrap')
        cherrystrap.GIT_BRANCH = kwargs.pop('git_branch', 'master')
        cherrystrap.GIT_UPSTREAM = kwargs.pop('git_upstream', None)
        cherrystrap.GIT_LOCAL = kwargs.pop('git_local', None)
        cherrystrap.GIT_STARTUP = kwargs.pop('git_startup', False) == 'on'
        try:
            cherrystrap.GIT_INTERVAL = int(kwargs.pop('git_interval', 0))
        except:
            cherrystrap.GIT_INTERVAL = 12
        cherrystrap.GIT_OVERRIDE = kwargs.pop('git_override', False) == 'on'

        if len(kwargs) != 0:
            logger.warn("Configuration update contained unexpected keywords: %s" % json.dumps(kwargs))

        cherrystrap.config_write()
        logger.info("All configuration settings posted successfully")
        return "{\"success\": \"All configuration settings posted successfully\"}"

    def DELETE(self, token=None):
        if token != cherrystrap.API_TOKEN:
            return "{\"error\": \"Invalid Token\"}"
        return "{\"error\": \"DELETE not available at this endpoint\"}"

class log(object):
    exposed = True

    def GET(self, token=None, draw=1, start=0, length=100, **kwargs):

        if token != cherrystrap.API_TOKEN:
            return "{\"error\": \"Invalid Token\"}"

        start = int(start)
        length = int(length)

        search = ""
        sortcolumn = 0
        sortdir = 'desc'

        if kwargs is not None:
            for key, value in kwargs.iteritems():
                if key == 'search[value]':
                    search = str(value).lower()
                if key == 'order[0][dir]':
                    sortdir = str(value)
                if key == 'order[0][column]':
                    sortcolumn = int(value)

        # Fix for column reordering without having to install a plugin
        if sortcolumn == 1:
            sortcolumn = 2
        elif sortcolumn == 2:
            sortcolumn = 3
        elif sortcolumn == 3:
            sortcolumn = 1

        filtered = []
        if search == "":
            filtered = cherrystrap.LOGLIST[::]
        else:
            filtered = list(set([row for row in cherrystrap.LOGLIST for column in row if search in column.lower()]))

        filtered.sort(key=lambda x:x[sortcolumn],reverse=sortdir == "desc")

        rows = filtered[start:(start+length)]
        rows = [[row[0],row[2],row[3],row[1]] for row in rows]

        dict = {'draw': draw,
                'recordsTotal':len(cherrystrap.LOGLIST),
                'recordsFiltered':len(filtered),
                'data':rows,
                }
        s = json.dumps(dict)
        return s

    def POST(self):
        if token != cherrystrap.API_TOKEN:
            return "{\"error\": \"Invalid Token\"}"
        return "{\"error\": \"POST not available at this endpoint\"}"

    def PUT(self):
        if token != cherrystrap.API_TOKEN:
            return "{\"error\": \"Invalid Token\"}"
        return "{\"error\": \"PUT not available at this endpoint\"}"

    def DELETE(self):
        if token != cherrystrap.API_TOKEN:
            return "{\"error\": \"Invalid Token\"}"
        return "{\"error\": \"DELETE not available at this endpoint\"}"
