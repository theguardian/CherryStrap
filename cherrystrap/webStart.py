import os, sys, cherrypy
import cherrystrap
from cherrystrap import logger
from cherrystrap.webServe import WebInterface
from cherrystrap.api import apiInterface
from cherrystrap.formatter import create_https_certificates

def initialize(options={}):

    verify_ssl = options['verify_ssl']
    if not verify_ssl:
        try:
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
        except:
            pass

    https_enabled = options['https_enabled']
    https_cert = options['https_cert']
    https_key = options['https_key']

    if https_enabled:
        # If either the HTTPS certificate or key do not exist, try to make
        # self-signed ones.
        if not (https_cert and os.path.exists(https_cert)) or not (https_key and os.path.exists(https_key)):
            if not create_https_certificates(https_cert, https_key):
                logger.warn("Unable to create certificate and key. Disabling " \
                    "HTTPS")
                https_enabled = False

        if not (os.path.exists(https_cert) and os.path.exists(https_key)):
            logger.warn("Disabled HTTPS because of missing certificate and " \
                "key.")
            https_enabled = False

    options_dict = {
        'log.screen':           False,
        'server.thread_pool':   10,
        'server.socket_port':   int(options['http_port']),
        'server.socket_host':   str(options['http_host']),
        'engine.autoreload.on': False,
        }

    if https_enabled:
        options_dict['server.ssl_certificate'] = https_cert
        options_dict['server.ssl_private_key'] = https_key
        protocol = "https"
    else:
        protocol = "http"

    logger.info("Starting CherryStrap on %s://%s:%d/" % (protocol,
        options['http_host'], options['http_port']))

    cherrypy.config.update(options_dict)

    webConf = {
        '/': {
            'tools.staticdir.root': os.path.join(cherrystrap.PROG_DIR, 'static')
        },
        '/interfaces':{
            'tools.staticdir.on': True,
            'tools.staticdir.dir': "interfaces"
        },
        '/images':{
            'tools.staticdir.on': True,
            'tools.staticdir.dir': "images"
        },
        '/css':{
            'tools.staticdir.on': True,
            'tools.staticdir.dir': "css"
        },
        '/js':{
            'tools.staticdir.on': True,
            'tools.staticdir.dir': "js"
        },
        '/favicon.ico':{
            'tools.staticfile.on': True,
            'tools.staticfile.filename': os.path.join(cherrystrap.PROG_DIR, 'static/images/favicon.ico')
        }
    }

    apiConf = {
        '/favicon.ico':{
            'tools.staticfile.on': True,
            'tools.staticfile.filename': os.path.join(cherrystrap.PROG_DIR, 'static/images/favicon.ico')
        }
    }

    # Prevent time-outs
    cherrypy.engine.timeout_monitor.unsubscribe()
    cherrypy.tree.mount(WebInterface(), options['http_root'], config = webConf)
    cherrypy.tree.mount(apiInterface(), options['http_root']+'/api/v1', config = apiConf)

    cherrypy.engine.autoreload.subscribe()

    try:
        cherrypy.process.servers.check_port(options['http_host'], options['http_port'])
        cherrypy.server.start()
        #cherrypy.engine.start() is good for dev mode, but breaks --daemon
    except IOError:
        print 'Failed to start on port: %i. Is something else running?' % (options['http_port'])
        sys.exit(0)

    cherrypy.server.wait()
