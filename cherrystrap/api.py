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

    def health(self, token=None):
        if token != cherrystrap.API_TOKEN:
            return "{\"error\": \"Invalid Token\"}"
        else:
            health_list = []
            health_array = collections.defaultdict()
            health_array['status'] = "OK"
            health_list.append(health_array)
            health_json = json.dumps(health_list)
            return health_json
    health.exposed = True
