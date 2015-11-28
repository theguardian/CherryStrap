import os
import cherrypy
from mako.template import Template
from mako.lookup import TemplateLookup
from mako import exceptions

import cherrystrap

def serve_template(templatename, **kwargs):

    interface_dir = os.path.join(str(cherrystrap.PROG_DIR), 'static/interfaces/')
    template_dir = os.path.join(str(interface_dir), cherrystrap.HTTP_LOOK)

    _hplookup = TemplateLookup(directories=[template_dir])

    try:
        template = _hplookup.get_template(templatename)
        return template.render(**kwargs)
    except:
        return exceptions.html_error_template().render()
