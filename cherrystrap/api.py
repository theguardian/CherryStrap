import collections
import cherrypy
import cherrystrap
from cherrypy import _cperror
from lib import simplejson as json
from cherrystrap import logger

class apiInterface(object):

    def error_page_404(status, message, traceback, version):
        return "{\"%s\": \"%s\"}" % (status, message)
    cherrypy.config.update({'error_page.404': error_page_404})

    def handle_error():
        cherrypy.response.status = 500
        logger.error("500 Error: %s" % _cperror.format_exc())
        cherrypy.response.body = ["{\"500 Server Error\": \"Sorry, an error occurred\"}"]

    _cp_config = {
        'error_page.404': error_page_404,
        'request.error_response': handle_error
    }

    # Returns JSON to display in logs view
    def getLog(self, draw=1, start=0, length=100, **kwargs):

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
    getLog.exposed = True

    def health(self, token=None):
        if token != cherrystrap.API_TOKEN:
            return "{\"error\": \"Invalid Token\"}"
        else:
            health_array = collections.defaultdict()
            health_array['status'] = "OK"
            health_json = json.dumps(health_array)
            return health_json
    health.exposed = True
