# -*- coding: utf-8 -*-
# $Id$

from slutils import logs
import cherrypy

logger = logs.loggerForModule("proxyf5_tool")


def proxyf5():
    """Tool for rewrite the sender ip address from the header set by the f5
    proxy"""

    header = 'X-Forwarded-For'
    request = cherrypy.request
    xff = request.headers.get(header)
    if xff:
        xff = xff.split(',')[-1].strip()
        request.remote.ip = xff

cherrypy.tools.proxyf5 = cherrypy.Tool('before_request_body', proxyf5)
