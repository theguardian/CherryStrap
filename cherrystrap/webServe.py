import os, cherrypy, urllib, collections
from cherrypy import _cperror
from lib import simplejson as json
from lib.passlib.hash import sha256_crypt
from auth import AuthController, require, member_of, name_is
from templating import serve_template

import threading, time

import cherrystrap

from cherrystrap import logger, formatter, database
from cherrystrap.formatter import checked

SESSION_KEY = '_cp_username'

class WebInterface(object):

    def error_page_404(status, message, traceback, version):
        status_msg = "%s - %s" % (status, message)
        return serve_template(templatename="index.html", title="404 - Page Not Found", msg=status_msg)
    cherrypy.config.update({'error_page.404': error_page_404})

    def handle_error():
        cherrypy.response.status = 500
        logger.error("500 Error: %s" % _cperror.format_exc())
        cherrypy.response.body = ["<html><body>Sorry, an error occured</body></html>"]

    _cp_config = {
        'tools.sessions.on': True,
        'tools.auth.on': True,
        'error_page.404': error_page_404,
        'request.error_response': handle_error
    }

    auth = AuthController()

    @require()
    def index(self):
        return serve_template(templatename="index.html", title="Home")
    index.exposed=True

    @require()
    def config(self):
        http_look_dir = os.path.join(cherrystrap.PROG_DIR, 'static/interfaces/')
        http_look_list = [ name for name in os.listdir(http_look_dir) if os.path.isdir(os.path.join(http_look_dir, name)) ]

        config = {
                    "app_name":         cherrystrap.APP_NAME,
                    "logdir":           cherrystrap.LOGDIR,
                    "http_host":        cherrystrap.HTTP_HOST,
                    "http_port":        cherrystrap.HTTP_PORT,
                    "https_enabled":    checked(cherrystrap.HTTPS_ENABLED),
                    "https_key":        cherrystrap.HTTPS_KEY,
                    "https_cert":       cherrystrap.HTTPS_CERT,
                    "verify_ssl":       checked(cherrystrap.VERIFY_SSL),
                    "launch_browser":   checked(cherrystrap.LAUNCH_BROWSER),
                    "http_user":        cherrystrap.HTTP_USER,
                    "http_pass":        cherrystrap.HTTP_PASS,
                    "http_look":        cherrystrap.HTTP_LOOK,
                    "http_look_list":   http_look_list,
                    "api_token":        cherrystrap.API_TOKEN,
                    "database_type":    cherrystrap.DATABASE_TYPE,
                    "mysql_host":       cherrystrap.MYSQL_HOST,
                    "mysql_port":       cherrystrap.MYSQL_PORT,
                    "mysql_user":       cherrystrap.MYSQL_USER,
                    "mysql_pass":       cherrystrap.MYSQL_PASS
                }
        return serve_template(templatename="config.html", title="Settings", config=config)
    config.exposed = True

    @require()
    def logs(self):
         return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)
    logs.exposed = True

    @require()
    def shutdown(self):
        cherrystrap.config_write()
        cherrystrap.SIGNAL = 'shutdown'
        message = 'shutting down ...'
        return serve_template(templatename="shutdown.html", title="Exit", message=message, timer=10)
        return page
    shutdown.exposed = True

    @require()
    def restart(self):
        cherrystrap.SIGNAL = 'restart'
        message = 'restarting ...'
        return serve_template(templatename="shutdown.html", title="Restart", message=message, timer=10)
    restart.exposed = True

    # Safe to delete this def, it's just there as a reference
    def template(self):
        return serve_template(templatename="template.html", title="Template Reference")
    template.exposed=True

    # Returns JSON to display in logs view
    def getLog(self,iDisplayStart=0,iDisplayLength=100,iSortCol_0=0,sSortDir_0="desc",sSearch="",**kwargs):

        iDisplayStart = int(iDisplayStart)
        iDisplayLength = int(iDisplayLength)

        filtered = []
        if sSearch == "":
            filtered = cherrystrap.LOGLIST[::]
        else:
            filtered = [row for row in cherrystrap.LOGLIST for column in row if sSearch in column]

        sortcolumn = 0
        if iSortCol_0 == '1':
            sortcolumn = 2
        elif iSortCol_0 == '2':
            sortcolumn = 1
        filtered.sort(key=lambda x:x[sortcolumn],reverse=sSortDir_0 == "desc")

        rows = filtered[iDisplayStart:(iDisplayStart+iDisplayLength)]
        rows = [[row[0],row[2],row[1]] for row in rows]

        dict = {'iTotalDisplayRecords':len(filtered),
                'iTotalRecords':len(cherrystrap.LOGLIST),
                'aaData':rows,
                }
        s = json.dumps(dict)
        return s
    getLog.exposed = True

    # AJAX def to update configuration file
    def configUpdate(self, app_name='CherryStrap', http_host='0.0.0.0',
    http_user=None, http_port=7889, http_pass=None, http_look=None,
    launch_browser=0, logdir=None, https_enabled=0, https_key=None,
    https_cert=None, verify_ssl=0, api_token=None, database_type='sqlite',
    mysql_host='localhost', mysql_port=3306, mysql_user=None, mysql_pass=None):

        cherrystrap.APP_NAME = app_name
        cherrystrap.LOGDIR = logdir
        cherrystrap.HTTP_HOST = http_host
        cherrystrap.HTTP_PORT = http_port
        cherrystrap.HTTPS_ENABLED = https_enabled
        cherrystrap.HTTPS_KEY = https_key
        cherrystrap.HTTPS_CERT = https_cert
        cherrystrap.VERIFY_SSL = verify_ssl
        cherrystrap.LAUNCH_BROWSER = launch_browser
        cherrystrap.HTTP_USER = http_user
        if http_pass != cherrystrap.HTTP_PASS:
            cherrystrap.HTTP_PASS = sha256_crypt.encrypt(http_pass)
        else:
            cherrystrap.HTTP_PASS = cherrystrap.HTTP_PASS
        cherrystrap.HTTP_LOOK = http_look
        cherrystrap.API_TOKEN = api_token
        cherrystrap.DATABASE_TYPE = database_type
        cherrystrap.MYSQL_HOST = mysql_host
        cherrystrap.MYSQL_PORT = mysql_port
        cherrystrap.MYSQL_USER = mysql_user
        if mysql_pass != cherrystrap.MYSQL_PASS:
            cherrystrap.MYSQL_PASS = formatter.encode('obscure', mysql_pass)
        else:
            cherrystrap.MYSQL_PASS = cherrystrap.MYSQL_PASS

        cherrystrap.config_write()
        logger.info("Configuration saved successfully")

    configUpdate.exposed = True
