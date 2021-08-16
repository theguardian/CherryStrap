import cherrypy, collections
import cherrystrap
import simplejson as json
from passlib.hash import sha256_crypt
from cherrystrap import logger, formatter, database

class settings(object):
    exposed = True

    def GET(self, token=None):

        if token != cherrystrap.API_TOKEN:
            return "{\"status\": \"error\", \"message\": \"Invalid Token\"}"

        configuration = {
            "server": {
                "appName":  cherrystrap.APP_NAME,
                "logDir": cherrystrap.LOGDIR,
                "httpHost": cherrystrap.HTTP_HOST,
                "httpPort": int(cherrystrap.HTTP_PORT),
                "sslEnabled": bool(cherrystrap.HTTPS_ENABLED),
                "sslKey": cherrystrap.HTTPS_KEY,
                "sslCert": cherrystrap.HTTPS_CERT,
                "sslVerify": bool(cherrystrap.VERIFY_SSL),
                "launchBrowser": bool(cherrystrap.LAUNCH_BROWSER)
            },
            "interface": {
                "httpUser": cherrystrap.HTTP_USER,
                "httpPass": cherrystrap.HTTP_PASS,
                "httpLook": cherrystrap.HTTP_LOOK,
                "apiToken": cherrystrap.API_TOKEN
            },
            "database": {
                "dbType": cherrystrap.DATABASE_TYPE,
                "mysqlHost": cherrystrap.MYSQL_HOST,
                "mysqlPort": int(cherrystrap.MYSQL_PORT),
                "mysqlUser": cherrystrap.MYSQL_USER,
                "mysqlPass": cherrystrap.MYSQL_PASS
            },
            "git": {
                "gitEnabled": bool(cherrystrap.GIT_ENABLED),
                "gitPath": cherrystrap.GIT_PATH,
                "gitUser": cherrystrap.GIT_USER,
                "gitRepo": cherrystrap.GIT_REPO,
                "gitBranch": cherrystrap.GIT_BRANCH,
                "gitUpstream": cherrystrap.GIT_UPSTREAM,
                "gitLocal": cherrystrap.GIT_LOCAL,
                "gitStartup": bool(cherrystrap.GIT_STARTUP),
                "gitInterval": int(cherrystrap.GIT_INTERVAL),
                "gitOverride": bool(cherrystrap.GIT_OVERRIDE)
            }
        }

        #===============================================================
        # Import a variable injector from your app's __init__.py
        try:
            from appfiles import injectApiConfigGet
            configuration.update(injectApiConfigGet())
        except Exception as e:
            logger.debug("There was a problem injection application variables into API-GET: %s" % e)
        #================================================================

        config = json.dumps(configuration)
        return config

    def POST(self, token=None):
        if token != cherrystrap.API_TOKEN:
            return "{\"status\": \"error\", \"message\": \"Invalid Token\"}"
        return "{\"status\": \"error\", \"message\": \"POST not available at this endpoint\"}"

    def PUT(self, token=None, **kwargs):

        if token != cherrystrap.API_TOKEN:
            return "{\"status\": \"error\", \"message\": \"Invalid Token\"}"

        errorList = []
        # Commented section below shows an example of how to receive
        # application/json formatted items. We'll keep it default
        # try:
        #     data = json.loads(cherrypy.request.body.read())
        #     for kvPair in data:
        #         dictName = kvPair['name']
        #         dictValue = kvPair['value']
        #         print dictName, dictValue
        # except:
        #     pass

        if 'appName' in kwargs:
            cherrystrap.APP_NAME = kwargs.pop('appName', 'CherryStrap')
        if 'logDir' in kwargs:
            cherrystrap.LOGDIR = kwargs.pop('logDir', None)
        if 'httpHost' in kwargs:
            cherrystrap.HTTP_HOST = kwargs.pop('httpHost', '0.0.0.0')
        if 'httpPort' in kwargs:
            try:
                cherrystrap.HTTP_PORT = int(kwargs.pop('httpPort', 7889))
            except:
                errorList.append("httpPort must be an integer")
                kwargs.pop('httpPort', 7889)

        if 'sslEnabled' in kwargs:
            cherrystrap.HTTPS_ENABLED = kwargs.pop('sslEnabled', False) == 'true'
        elif 'sslEnabledHidden' in kwargs:
            cherrystrap.HTTPS_ENABLED = kwargs.pop('sslEnabledHidden', False) == 'true'
        if 'sslKey' in kwargs:
            cherrystrap.HTTPS_KEY = kwargs.pop('sslKey', 'keys/server.key')
        if 'sslCert' in kwargs:
            cherrystrap.HTTPS_CERT = kwargs.pop('sslCert', 'keys/server.crt')
        if 'sslVerify' in kwargs:
            cherrystrap.VERIFY_SSL = kwargs.pop('sslVerify', True) == 'true'
        elif 'sslVerifyHidden' in kwargs:
            cherrystrap.VERIFY_SSL = kwargs.pop('sslVerifyHidden', True) == 'true'
        if 'launchBrowser' in kwargs:
            cherrystrap.LAUNCH_BROWSER = kwargs.pop('launchBrowser', False) == 'true'
        elif 'launchBrowserHidden' in kwargs:
            cherrystrap.LAUNCH_BROWSER = kwargs.pop('launchBrowserHidden', False) == 'true'

        if 'httpUser' in kwargs:
            cherrystrap.HTTP_USER = kwargs.pop('httpUser', None)
        if 'httpPass' in kwargs:
            httpPassProcess = kwargs.pop('httpPass', None)
            if httpPassProcess != cherrystrap.HTTP_PASS and httpPassProcess != "":
                try:
                    cherrystrap.HTTP_PASS = sha256_crypt.encrypt(httpPassProcess)
                except Exception as e:
                    logger.error('There was a problem generating password hash: %s' % e)
            elif httpPassProcess == "":
                cherrystrap.HTTP_PASS = ""
        if 'httpLook' in kwargs:
            cherrystrap.HTTP_LOOK = kwargs.pop('httpLook', 'bootstrap')
        if 'apiToken' in kwargs:
            cherrystrap.API_TOKEN = kwargs.pop('apiToken', None)

        if 'dbType' in kwargs:
            cherrystrap.DATABASE_TYPE = kwargs.pop('dbType', '')
        if 'mysqlHost' in kwargs:
            cherrystrap.MYSQL_HOST = kwargs.pop('mysqlHost', 'localhost')
        if 'mysqlPort' in kwargs:
            try:
                cherrystrap.MYSQL_PORT = int(kwargs.pop('mysqlPort', 3306))
            except:
                errorList.append("mysqlPort must be an integer")
                kwargs.pop('MySQLPort', 3306)
        if 'mysqlUser' in kwargs:
            cherrystrap.MYSQL_USER = kwargs.pop('mysqlUser', None)
        if 'mysqlPass' in kwargs:
            mysqlPassProcess = kwargs.pop('mysqlPass', None)
            if mysqlPassProcess != cherrystrap.MYSQL_PASS and mysqlPassProcess != "":
                try:
                    cherrystrap.MYSQL_PASS = formatter.encode('obscure', mysqlPassProcess)
                except Exception as e:
                    logger.error('There was a problem encoding MySQL password: %s' % e)
            elif mysqlPassProcess == "":
                cherrystrap.MYSQL_PASS = ""

        if 'gitEnabled' in kwargs:
            cherrystrap.GIT_ENABLED = kwargs.pop('gitEnabled', False) == 'true'
        elif 'gitEnabledHidden' in kwargs:
            cherrystrap.GIT_ENABLED = kwargs.pop('gitEnabledHidden', False) == 'true'
        if 'gitPath' in kwargs:
            cherrystrap.GIT_PATH = kwargs.pop('gitPath', None)
        if 'gitUser' in kwargs:
            cherrystrap.GIT_USER = kwargs.pop('gitUser', 'theguardian')
        if 'gitRepo' in kwargs:
            cherrystrap.GIT_REPO = kwargs.pop('gitRepo', 'CherryStrap')
        if 'gitBranch' in kwargs:
            cherrystrap.GIT_BRANCH = kwargs.pop('gitBranch', 'master')
        if 'gitUpstream' in kwargs:
            cherrystrap.GIT_UPSTREAM = kwargs.pop('gitUpstream', None)
        if 'gitLocal' in kwargs:
            cherrystrap.GIT_LOCAL = kwargs.pop('gitLocal', None)
        if 'gitStartup' in kwargs:
            cherrystrap.GIT_STARTUP = kwargs.pop('gitStartup', False) == 'true'
        elif 'gitStartupHidden' in kwargs:
            cherrystrap.GIT_STARTUP = kwargs.pop('gitStartupHidden', False) == 'true'
        if 'gitInterval' in kwargs:
            try:
                cherrystrap.GIT_INTERVAL = int(kwargs.pop('gitInterval', 0))
            except:
                cherrystrap.GIT_INTERVAL = 12
                errorList.append("gitInterval must be an integer")
                kwargs.pop('gitInterval', 12)
        if 'gitOverride' in kwargs:
            cherrystrap.GIT_OVERRIDE = kwargs.pop('gitOverride', False) == 'true'
        elif 'gitOverrideHidden' in kwargs:
            cherrystrap.GIT_OVERRIDE = kwargs.pop('gitOverrideHidden', False) == 'true'

        #===============================================================
        # Import a variable injector from your app's __init__.py
        try:
            from appfiles import injectApiConfigPut
            kwargs, errorList = injectApiConfigPut(kwargs, errorList)
        except Exception as e:
            logger.debug("There was a problem injection application variables into API-PUT: %s" % e)
        #================================================================

        if len(kwargs) != 0:
            for key, value in kwargs.items():
                errorList.append("Key %s not expected" % key)

        cherrystrap.config_write()
        if not errorList:
            logger.info("All configuration settings successfully updated")
            return "{\"status\": \"success\", \
                \"message\": \"All configuration settings successfully updated\"}"
        else:
            logger.warn("The following error(s) occurred while attempting to update settings: %s" % errorList)
            return "{\"status\": \"warning\", \
                \"message\": \"The following error(s) occurred while attempting to update settings: %s\"}" % errorList

    def DELETE(self, token=None):
        if token != cherrystrap.API_TOKEN:
            return "{\"status\": \"error\", \"message\": \"Invalid Token\"}"
        return "{\"status\": \"error\", \"message\": \"DELETE not available at this endpoint\"}"

class applicationlog(object):
    exposed = True

    def GET(self, token=None, draw=1, start=0, length=100, **kwargs):

        if token != cherrystrap.API_TOKEN:
            return "{\"status\": \"error\", \"message\": \"Invalid Token\"}"

        start = int(start)
        length = int(length)

        search = ""
        sortcolumn = 0
        sortdir = 'desc'

        if kwargs is not None:
            for key, value in kwargs.items():
                if key == 'search[value]':
                    search = str(value).lower()
                if key == 'order[0][dir]':
                    sortdir = str(value)
                if key == 'order[0][column]':
                    sortcolumn = int(value)

        # Fix for column reordering without having to install a plugin
        newOrder = [0,2,3,1]
        logArr = []
        for line in cherrystrap.LOGLIST:
            logList = [ line[i] for i in newOrder]
            logArr.append(tuple(logList))

        filtered = []
        if search == "":
            filtered = logArr
        else:
            filtered = list(set([row for row in logArr for column in row if search in column.lower()]))

        filtered.sort(key=lambda x:x[sortcolumn],reverse=sortdir == "desc")

        rows = filtered[start:(start+length)]

        dict = {'draw': draw,
                'recordsTotal':len(logArr),
                'recordsFiltered':len(filtered),
                'data':rows,
                }
        s = json.dumps(dict)
        return s

    def POST(self):
        if token != cherrystrap.API_TOKEN:
            return "{\"status\": \"error\", \"message\": \"Invalid Token\"}"
        return "{\"status\": \"error\", \"message\": \"POST not available at this endpoint\"}"

    def PUT(self):
        if token != cherrystrap.API_TOKEN:
            return "{\"status\": \"error\", \"message\": \"Invalid Token\"}"
        return "{\"status\": \"error\", \"message\": \"PUT not available at this endpoint\"}"

    def DELETE(self):
        if token != cherrystrap.API_TOKEN:
            return "{\"status\": \"error\", \"message\": \"Invalid Token\"}"
        return "{\"status\": \"error\", \"message\": \"DELETE not available at this endpoint\"}"
