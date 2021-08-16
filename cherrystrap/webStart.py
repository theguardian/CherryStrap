import os, sys, cherrypy
import cherrystrap
import portend
from cherrystrap import logger
from cherrystrap.webServe import WebInterface
from cherrystrap import apiServe
from cherrystrap.formatter import create_https_certificates

def initialize(options={}):

    https_enabled = options['sslEnabled']
    https_cert = options['sslCert']
    https_key = options['sslKey']

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
        'server.socket_port':   int(options['httpPort']),
        'server.socket_host':   str(options['httpHost']),
        'engine.autoreload.on': False,
        }

    if https_enabled:
        options_dict['server.ssl_certificate'] = https_cert
        options_dict['server.ssl_private_key'] = https_key
        protocol = "https"
    else:
        protocol = "http"

    logger.info("Starting %s on %s://%s:%d/" % (cherrystrap.APP_NAME, protocol,
        options['httpHost'], options['httpPort']))

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
        '/fonts':{
            'tools.staticdir.on': True,
            'tools.staticdir.dir': "fonts"
        },
        '/favicon.ico':{
            'tools.staticfile.on': True,
            'tools.staticfile.filename': os.path.join(cherrystrap.PROG_DIR, 'static/images/favicon.ico')
        }
    }

    # Prevent time-outs
    # deprecated
    # cherrypy.engine.timeout_monitor.unsubscribe()
    cherrypy.tree.mount(WebInterface(), options['httpRoot'], config = webConf)

    # Load API endpoints
    cherrypy.tree.mount(apiServe.settings(), cherrystrap.HTTP_ROOT+'/api/v1/settings',
        {'/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}})
    cherrypy.tree.mount(apiServe.applicationlog(), cherrystrap.HTTP_ROOT+'/api/v1/applicationlog',
        {'/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}})
    cherrypy.engine.autoreload.subscribe()

    try:
        portend.Checker().assert_free(options['httpHost'], options['httpPort'])
        cherrypy.server.start()
        #cherrypy.engine.start() is good for dev mode, but breaks --daemon
    except IOError:
        print ('Failed to start on port: %i. Is something else running?' % (options['httpPort']))
        sys.exit(0)

    cherrypy.server.wait()
