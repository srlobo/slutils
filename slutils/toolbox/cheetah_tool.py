# -*- coding: utf-8 -*-
# $Id$

"""Uso:
    class Test_Cheetah_Tool(object):
        @cp.expose
        @cp.tools.cheetah(template='Greetings')
        def index(self, username=None, **kwargs):
            return {'username': username}
"""

import logs
import cherrypy
import os

logger = logs.loggerForModule("cheetah_tool")


class CheetahHandler(cherrypy.dispatch.LateParamPageHandler):
    def __init__(self, template, next_handler, templatemodule=None):
        self.next_handler = next_handler
        if template is None:
            cherrypy.request.config.get('tools.cheetah.template', None)
        if template is None:
            logger.info("Usamos la plantilla por defecto")
            # template = "Templates.decorative"
        tmparr = template.split('.')
        if len(tmparr) != 1:
            self.template = tmparr[-1]
            self.modulename = '.'.join(tmparr)
        else:
            self.modulename = template
            self.template = template

    def __call__(self):
        env = globals().copy()
        env.update(self.next_handler())
        tmpl = getattr(__import__(self.modulename, globals(), locals(),
                                  [self.template], -1), self.template)
        variables_comunes = obtener_variables_comunes()
        env.update(variables_comunes)
        return str(tmpl(searchList=[env]))


class CheetahLoader(object):
    def __call__(self, template=None, title=None,
                 templatemodule=None, **kwargs):
        logger.debug("template: %s" % template)
        logger.debug("title: %s" % title)
        if not title:
            logger.info("No está puesto el título")
        cherrypy.request.handler = CheetahHandler(template,
                                                  cherrypy.request.handler)


main = CheetahLoader()
cherrypy.tools.cheetah = cherrypy.Tool('on_start_resource', main)


def obtener_variables_comunes():
    import datetime
    import locale

    ret = {}
    try:
        ret["identificacion"] = cherrypy.request.login
        if ret["identificacion"]:
            ret["usuario"] = "??"
            if "givenName" in cherrypy.session["userdata"]:
                ret["usuario"] = cherrypy.session["userdata"]["givenName"]
    except:
        logger.debug("Problemas obteniendo datos de usuario en cheetah_tool")
        ret["usuario"] = "??"

    locale.setlocale(locale.LC_ALL, ('es_ES', 'UTF-8'))
    ret["fecha"] = datetime.datetime.now().strftime("%e de %B, %Y")
    ret["titulo"] = cherrypy.request.config.get("tools.cheetah.title",
                                                "Aplicación sin título")

    menu = cherrypy.request.config.get('tools.cheetah.menu_list', None)
    if menu:
        ret["sidebar_menu"] = menu

    menu = cherrypy.request.config.get('tools.cheetah.menu_function', None)
    if menu:
        ret["sidebar_menu"] = menu()

    ret["appversion"] = cherrypy.request.config.get(
        'tools.cheetah.appversion', "")

    try:
        ret["krb"] = cherrypy.session.get("krb", False)
    except:
        ret["krb"] = False

    return ret


class Emptyapp:
    pass

rsc_dir = os.path.join(os.path.dirname(__file__), 'Templates', 'resources')


conf = {
    '/': {
        'tools.auth.on': False,
        'tools.sessions.on': False,
        'tools.staticdir.on': True,
        'tools.staticdir.dir': rsc_dir,
    },
    '/javascript': {
        'tools.auth.on': False,
        'tools.sessions.on': False,
        'tools.staticdir.match': "^/javascript/",
        'tools.staticdir.on': True,
        'tools.staticdir.dir': "/usr/share/javascript/",
    },


}

cherrypy.tree.mount(Emptyapp(), "/resources", conf)
