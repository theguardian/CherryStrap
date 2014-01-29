import os, cherrypy, urllib
import simplejson

from mako.template import Template
from mako.lookup import TemplateLookup
from mako import exceptions

import threading, time

import cherrystrap

from cherrystrap import logger, formatter, database
from cherrystrap.formatter import checked

def serve_template(templatename, **kwargs):

    interface_dir = os.path.join(str(cherrystrap.PROG_DIR), 'data/interfaces/')
    template_dir = os.path.join(str(interface_dir), cherrystrap.HTTP_LOOK)

    _hplookup = TemplateLookup(directories=[template_dir])

    try:
        template = _hplookup.get_template(templatename)
        return template.render(**kwargs)
    except:
        return exceptions.html_error_template().render()


class WebInterface(object):

    def index(self):
        return serve_template(templatename="index.html", title="Home")
    index.exposed=True

    def config(self):
        http_look_dir = os.path.join(cherrystrap.PROG_DIR, 'data/interfaces/')
        http_look_list = [ name for name in os.listdir(http_look_dir) if os.path.isdir(os.path.join(http_look_dir, name)) ]

        config = {
                    "server_name":      cherrystrap.SERVER_NAME,
                    "http_host":        cherrystrap.HTTP_HOST,
                    "http_user":        cherrystrap.HTTP_USER,
                    "http_port":        cherrystrap.HTTP_PORT,
                    "http_pass":        cherrystrap.HTTP_PASS,
                    "http_look":        cherrystrap.HTTP_LOOK,
                    "http_look_list":   http_look_list,
                    "launch_browser":   checked(cherrystrap.LAUNCH_BROWSER),
                    "logdir":           cherrystrap.LOGDIR
                }
        return serve_template(templatename="config.html", title="Settings", config=config)    
    config.exposed = True

    def configUpdate(self, server_name="Server", http_host='0.0.0.0', http_user=None, http_port=7889, http_pass=None, http_look=None, launch_browser=0, logdir=None):

        cherrystrap.SERVER_NAME = server_name
        cherrystrap.HTTP_HOST = http_host
        cherrystrap.HTTP_PORT = http_port
        cherrystrap.HTTP_USER = http_user
        cherrystrap.HTTP_PASS = http_pass
        cherrystrap.HTTP_LOOK = http_look
        cherrystrap.LAUNCH_BROWSER = launch_browser
        cherrystrap.LOGDIR = logdir

        cherrystrap.config_write()

    configUpdate.exposed = True

    def logs(self):
         return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)
    logs.exposed = True

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
        s = simplejson.dumps(dict)
        return s
    getLog.exposed = True

    def template_reference(self):
        return serve_template(templatename="template.html", title="Template Reference")
    template_reference.exposed=True

    def shutdown(self):
        cherrystrap.config_write()
        cherrystrap.SIGNAL = 'shutdown'
        message = 'shutting down ...'
        return serve_template(templatename="shutdown.html", title="Exit", message=message, timer=10)
        return page
    shutdown.exposed = True

    def restart(self):
        cherrystrap.SIGNAL = 'restart'
        message = 'restarting ...'
        return serve_template(templatename="shutdown.html", title="Restart", message=message, timer=10)
    restart.exposed = True