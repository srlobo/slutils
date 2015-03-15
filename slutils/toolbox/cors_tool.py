# -*- coding: utf-8 -*-

"""cors_tool.py

Utilidad para agregar cors a cherrypy como tool.
De momento la implementación es trivial, simplemente permite que todo el mundo
recoja datos de nuestro servidor.
Para activarlo, simplemente:

cherrypy.tool.CORS.on: True

en la configuración. También se puede activar por aplicacion, en la
configuración local.

"""

from slutils import logs
import cherrypy

logger = logs.loggerForModule("cors_tool")


def CORS():
    cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"
    
cherrypy.tools.cors = cherrypy.Tool('before_finalize', CORS)
