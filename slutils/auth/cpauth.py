#!/usr/bin/python
# -*- coding: utf-8 -*-

import cherrypy
import base
import threading
from  import logs

__BASE_AUTH_URI__ = '/auth'
SESSION_LOGIN_KEY = 'login'
SESSION_USERDATA_KEY = 'userdata'
SESSION_GROUP_KEY = 'groups'
MAX_REDIRECT = 5  # El máximo absoluto debería ser 21

UDATA_LOCK = threading.Lock()


# Sacado de http://tools.cherrypy.org/wiki/AuthenticationAndAccessRestrictions
logger = logs.loggerForModule("ptauth.cpauth")


def check_auth(*args, **kwargs):
    """A tool that looks in config for 'auth.require'. If found and it
    is not None, a login is required and the entry is evaluated as a list of
    conditions that the user must fulfill"""

    logger.debug("URL: %s", cherrypy.url())

    conditions = cherrypy.request.config.get('auth.require', None)
    if conditions:
        username = cherrypy.session.get(SESSION_LOGIN_KEY)
        if username:
            logger.debug("Redirects: %d", cherrypy.session["redirects"])
            # Controlamos que las redirects no se vayan de madre
            if cherrypy.session["redirects"] > MAX_REDIRECT:
                cherrypy.session["redirects"] += 1
                logger.debug("Número máximo de redirecciones alcanzadas," +
                             "salimos")
                redirect_url = __BASE_AUTH_URI__ + "/permissionError"
                logger.debug("URL de redirección: %s", redirect_url)
                raise cherrypy.HTTPRedirect(redirect_url)

            cherrypy.request.login = username
            for condition in conditions:
                # A condition is just a callable that returns true or false
                if not condition():
                    logger.debug("Una condicion ha devuelto False -> " +
                                 "error de permisos")
                    return_url = __BASE_AUTH_URI__ + "/permissionError"

                    cherrypy.session["redirects"] += 1
                    raise cherrypy.HTTPRedirect(return_url)
        else:
            url = __BASE_AUTH_URI__
            url += "/krb/?return_url=%s" % cherrypy.url()
            url += "&" + kwargs2param(cherrypy.request.params)
            logger.debug("redireccionando a %s", url)
            raise cherrypy.HTTPRedirect(url)

    cherrypy.session["redirects"] = 0

cherrypy.tools.auth = cherrypy.Tool('before_handler', check_auth)


def require(*conditions):
    """A decorator that appends conditions to the auth.require config
    variable."""
    def decorate(f):
        if not hasattr(f, '_cp_config'):
            f._cp_config = dict()
        if 'auth.require' not in f._cp_config:
            f._cp_config['auth.require'] = []
        f._cp_config['auth.require'].extend(conditions)
        return f
    return decorate


# Conditions are callables that return True
# if the user fulfills the conditions they define, False otherwise
#
# They can access the current username as cherrypy.request.login
#
# Define those at will however suits the application.

def member_of(groupname):
    def check():
        # replace with actual check if <username> is in <groupname>
        logger.debug("Comprobando si el usuario %s esta en %s" %
                     (cherrypy.request.login, groupname))
        # logger.debug(cherrypy.session.get(SESSION_GROUP_KEY, ()))
        user_groups = cherrypy.session.get(SESSION_GROUP_KEY, {})
        if groupname in user_groups.keys() or \
                groupname in user_groups.values():
            return True
        else:
            return False

    return check


def name_is(reqd_username):
    return lambda: reqd_username.upper() == cherrypy.request.login.upper()

# These might be handy


def any_of(*conditions):
    """Returns True if any of the conditions match"""
    def check():
        for c in conditions:
            if c():
                return True
        return False
    return check


# By default all conditions are required, but this might still be
# needed if you want to use it inside of an any_of(...) condition
def all_of(*conditions):
    """Returns True if all of the conditions match"""
    def check():
        for c in conditions:
            if not c():
                return False
        return True
    return check


class auth(object):
    """Decorador para permitir o no la entrada en un método, dependiendo de
    los grupos a los que pertenezca el usuario"""
    def __call__(self):
        pass


class CherrypyAuthClass:
    """Clase que responde a las urls de autenticacion"""

    def __init__(self):
        self.required_groups = ()
        self.banned_groups = ()

    @cherrypy.tools.cheetah()
    @cherrypy.expose
    def info(self):
        vuelta = {}
        vuelta["subtitulo"] = "Información de autenticación"
        body = u"<ul>\n"
        body += "<li>Login: %s</li>\n" % \
            unicode(cherrypy.session.get(SESSION_LOGIN_KEY, "No hay login"))
        body += "<li>Info: "
        info = cherrypy.session.get(SESSION_USERDATA_KEY, None)
        if not info:
            body += "No hay info"
        else:
            body += "<ul>\n"
            for el in info.iteritems():
                a = u"<li>%s: %s</li>\n" % (el[0].decode("utf8"),
                                            el[1].decode("utf8"))
                body += a
            body += "</ul>\n"

        body += "</li>\n"
        body += "<li>Grupos:\n"
        try:
            body += "<ul>\n"
            for group in cherrypy.session[SESSION_GROUP_KEY].iteritems():
                body += "<li>(%s, %s)</li>\n" % (group[0].decode("utf8"),
                                                 group[1].decode("utf8"))

            body += "</ul>\n"
        except:
            body += "No hay grupos<br>\n"

        vuelta["body"] = body

        return vuelta

    @cherrypy.tools.cheetah()
    @cherrypy.expose
    def index(self, **kwargs):
        """Metodo para hacer la autenticacion etc"""

        # La url de vuelta está indicada en un argumento (GET o POST), si no
        # existe coge el referer, y si no va al raiz de la aplicación.
        return_url = kwargs.get("return_url",
                                cherrypy.request.headers.get('Referer', "/"))

        # Estamos volviendo del krb?
        krb = kwargs.get("krb", False)

        logger.debug("URL de vuelta: %s" % return_url)
        logger.debug("kwargs %s" % kwargs.get("return_url", "no hay"))
        # logger.debug("headers %s" % cherrypy.request.headers.get("Referer",
        # "no hay"))
        # for header in cherrypy.request.headers.iteritems():
        #    logger.debug("Item: %s, %s" % header)
        # error_msg = ""

        # Primero comprobamos que no tengamos una sesion abierta
        if cherrypy.session.get(SESSION_LOGIN_KEY, False):
            logger.debug("session pillada, login: %s" %
                         cherrypy.session.get(SESSION_LOGIN_KEY))
            # Si tenemos una sesion abierta comprobamos si hay algun problema

            # Ahora comprobamos que no estemos haciendo una redireccion sobre
            # la misma página. La situación en la que se da esto es cuando no
            # se tienen permisos (por grupos normalmente).
            cherrypy.session["redirects"] += 1
            if(return_url == cherrypy.url()):
                raise cherrypy.HTTPRedirect(cherrypy.url("permissionError"))

            # Componemos la url con los parametros correspondientes
            url = return_url + "?" + kwargs2param(kwargs)
            logger.debug("Redireccionando a %s", url)
            raise cherrypy.HTTPRedirect(url)

        # Si tenemos activada la autenticacion por kerberos, hacemos la magia
        # aqui
        if cherrypy.request.config.get('auth.kerberos', False):
            # Si venimos de krb -> seguimos
            if not krb:
                url = "/krb?return_url=" + return_url
                url += "&" + kwargs2param(kwargs)
                logger.debug("Configurada auth kerberos, " +
                             "redireccionando, return_url: %s", url)
                raise cherrypy.HTTPRedirect(cherrypy.url(url))

        user = kwargs.get('user', False)
        logger.debug("User: %s" % user)
        password = kwargs.get('password', False)
        # logger.debug("Password: %s" % password)

        if (not user or not password):
            logger.debug("not user: %s" % str(not user))
            logger.debug("not password: %s" % str(not password))

            return self.loginBox(return_url=return_url, krb=krb)

        try:
            if(not self.doLocalLogin(user, password)):
                error_msg = "Password incorrecta"
                return self.loginBox(return_url=return_url,
                                     error_msg=error_msg, krb=krb)

        except Exception, e:
            logger.debug("Excepcion: %s" % str(e))
            error_msg = "Password incorrecta"
            return self.loginBox(return_url=return_url,
                                 error_msg=error_msg, krb=krb)

        # No debemos llegar aqui
        logger.debug("Prueba superada, estamos dentro")
        cherrypy.session["redirects"] += 1
        url = return_url
        url += "?" + kwargs2param(kwargs)
        raise cherrypy.HTTPRedirect(url)

    def doLocalLogin(self, user, passwd, realuser=False, krb=False):
        """Metodo para hacer la autenticacion etc"""
        logger.debug("doLocalLogin")

        logger.debug("realuser antes: %s", realuser)
        if not realuser:
            realuser = user
        else:  # Usuarios de tipo a142257@GRUPO.CM.ES
            realuser = realuser.split('@')[0]
        logger.debug("realuser despues: %s", realuser)

        try:
            logger.debug("Intentamos adquirir lock udata (check)")
            UDATA_LOCK.acquire()
            logger.debug("Conseguido lock udata (check)")
            passiscorrect = base.checkUser(user, passwd)
        except Exception:
            logger.exception("udata (check)")
            passiscorrect = False
        finally:
            logger.debug("Soltamos lock udata (check)")
            UDATA_LOCK.release()
            logger.debug("Lock udata suelto (check)")

        if not passiscorrect:
            logger.debug("La password no es válida")
            return False

        # A partir de aqui el usuario esta validado. Para obtener los grupos lo
        # intentamos con el usuario descrito como ldap.user (si existe). Si no,
        # lo hacemos directamente con el usuario dado, aunque puede fallar.
        ldap_user = cherrypy.request.config.get('auth.ldap_user', False)
        ldap_password = cherrypy.request.config.get('auth.ldap_password',
                                                    False)
        if ldap_user and ldap_password:
            user = ldap_user
            passwd = ldap_password

        try:
            logger.debug("Intentamos adquirir lock udata")
            UDATA_LOCK.acquire()
            logger.debug("Conseguido lock udata")
            udata = base.obtainUserData(user, passwd, realuser)
        except Exception:
            logger.exception("udata")
            udata = False
        finally:
            logger.debug("Soltamos lock udata")
            UDATA_LOCK.release()
            logger.debug("Lock udata suelto")

        if udata:
            cherrypy.session[SESSION_LOGIN_KEY] = realuser
            cherrypy.session[SESSION_USERDATA_KEY] = udata[0]
            cherrypy.session[SESSION_GROUP_KEY] = udata[1]
            cherrypy.session["krb"] = krb
            cherrypy.session["redirects"] = 0

            return True
        else:
            return False

    def loginBox(self, **kwargs):
        """Dibuja un cuadro con el login"""

        logger.debug("En loginbox")
        vuelta = {}
        vuelta["header"] = """
<script type="text/javascript"
    src="/resources/javascript/jquery/jquery.min.js">
</script>
<link type="text/css"
    href="/resources/javascript/jquery-ui/css/smoothness/jquery-ui.css"
    rel="stylesheet" />
<script language="javascript" type="text/javascript"
    src="/resources/javascript/jquery-ui/jquery-ui.js">
</script>
<script type="text/javascript">
$(document).ready(function() {
    $("input#user").focus();
    $("input#enviar").button();
});
</script>
"""
        vuelta["subtitulo"] = "Autenticación"
        body = u"""
<script type="text/javascript">
pattern = new RegExp('^%(thisurl)s')
if(! String(window.location).match(pattern))
    window.location = '%(thisurl)s';
</script>
""" % {'thisurl': cherrypy.url('/')}

        if kwargs.get("error_msg", False):
            body += kwargs.get("error_msg")

        if cherrypy.session.get(SESSION_LOGIN_KEY, False):
            body += u"""Bienvenido, %s<br>""" % \
                cherrypy.session.get(SESSION_LOGIN_KEY)
            body += u"""<a href="doLogout">Salir</a><br>"""
        else:
            body += u"""<div id="loginform">\n"""
            body += u"""<form action="index" method="post">\n"""
            body += u"""<fieldset>\n"""
            body += u"""Autenticación con usuario\n"""
            body += u"""<ul>\n
    <li> <label>Usuario</label><input id="user" type="text" name="user">
    </li>
    <li> <label>Password</label>
        <input id="password" type="password" name="password">
    </li>
</ul>\n"""
            body += u"""<input id="enviar" type="submit" name="enviar"
value="Enviar">\n"""
            body += u"""</fieldset>\n"""
            body += u"""</div>\n"""

            if kwargs.get("return_url", False):
                tmp = u'<input type="hidden" name="return_url" value="%s">\n'
                tmp = tmp % kwargs.get("return_url")
                body += tmp

            if kwargs.get("krb", False):
                tmp = u"""<input type="hidden" name="krb" value="%s">\n"""
                tmp = tmp % kwargs.get("krb")
                body += tmp

        body += u"""</form>\n"""

        vuelta["body"] = body

        logger.debug("Saliendo de loginbox")
        return vuelta

    @cherrypy.expose
    def doLogout(self, **kwargs):
        """Metodo que destruye la sesion de usuario actual"""

        logger.debug("Entrando en doLogout")

        try:
            cherrypy.session.delete()
            logger.debug("Sesion borrada")
        except:
            pass

        try:
            cherrypy.lib.sessions.expire()
            logger.debug("Sesion expirada")
        except:
            pass

        if kwargs.get("krb", False):
            args = "?krb=%s" % kwargs["krb"]
            raise cherrypy.HTTPRedirect(cherrypy.url('/') + args)

        logger.debug("Redireccion doLogout")

        raise cherrypy.HTTPRedirect('/')

    @cherrypy.tools.cheetah()
    @cherrypy.expose
    def permissionError(self, **kwargs):
        """Metodo que informa al usuario que no tiene permiso"""

        vuelta = {}
        vuelta["subtitulo"] = "Error en Autenticación"

        vuelta["body"] = "No tiene permiso para ver la página solicitada<br>"
        vuelta["body"] += 'Puede <a href="%s">cerrar sesión</a>, intentar '
        vuelta["body"] = vuelta["body"] % cherrypy.url("doLogout")
        vuelta["body"] += '<a href="javascript:history.go(-1)">volver</a>'
        vuelta["body"] += ' o intentar <a href="%s?krb=1">abrir una sesión ' + \
            'ignorando SSO</a>.'

        vuelta["body"] = vuelta["body"] % cherrypy.url("doLogout")

        return vuelta

    # @cherrypy.tools.cheetah()
    @cherrypy.expose
    def krb(self, **kwargs):
        """Metodo para obtener la auth de kerberos"""

        logger.debug("Entramos en krb")
        return_url = kwargs.get("return_url", "/")

        # Si tenemos desactivado el kerberos, ni entramos aqui.
        if not cherrypy.request.config.get('auth.kerberos', False):
            url = __BASE_AUTH_URI__ + "/?return_url=" + return_url
            url += "&" + kwargs2param(kwargs)
            raise cherrypy.HTTPRedirect(url)

        try:

            realuser = cherrypy.request.login

            user = cherrypy.request.config.get('auth.ldap_user', False)
            password = cherrypy.request.config.get('auth.ldap_password', False)

            logger.debug("user: %s, pass: %s, realuser: %s",
                         user, password, realuser)

            if user and password and realuser:
                logger.debug("user, password y realuser")
                if self.doLocalLogin(user, password, realuser, krb=True):
                    url = return_url + "?" + kwargs2param(kwargs)
                    logger.debug("redireccionando a %s" % url)
                    raise cherrypy.HTTPRedirect(url)

        except cherrypy.HTTPRedirect, e:
            raise e
        except:
            logger.exception("krb")

        url = "/?return_url=%s&krb=1&" % return_url
        url += kwargs2param(kwargs)
        raise cherrypy.HTTPRedirect(cherrypy.url(url))


def kwargs2param(kwargs):
    # Parámetros que no se deben propagar
    banned_params = ["krb", "return_url", "password", "user"]
    for par in banned_params:
        if par in kwargs:
            del kwargs[par]

    res = []
    for key_val in kwargs.iteritems():
        res.append("%s=%s" % key_val)

    logger.debug("kw2pa: %s", str(res))
    return "&".join(res)

conf = {
    '/': {
        'tools.sessions.on': True,
    },
}

cpauth = CherrypyAuthClass()

if __BASE_AUTH_URI__ in cherrypy.tree.apps:
    logger.debug("El path %s ya está ocupado, no añadimos la app auth" %
                 __BASE_AUTH_URI__)
else:
    cherrypy.tree.mount(cpauth, __BASE_AUTH_URI__, conf)

cherrypy.config.update({
    'tools.sessions.storage_path': "/tmp/",
    'tools.sessions.storage_type': "file",
})
