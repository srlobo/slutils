# -*- coding: utf-8 -*-
import cherrypy
import sqlalchemy
import sljson as json
import logs

logger = logs.loggerForModule("slutils.rest")

# Mirar esto:
# http://code.activestate.com/recipes/444766-cherrypy-restresource/


class RestInterface(object):
    _methods = ["GET", "PUT", "DELETE", "POST", "OPTIONS"]

    logger = logger

    def check_permission(self, method):
        """Devuelve True o False si hay permiso para hacer put"""
        return True

    @cherrypy.tools.response_headers(
        headers=[('Content-Type', 'application/json')])
    @cherrypy.expose
    def default(self, *args, **kwargs):
        """Punto de entrada"""
        if cherrypy.request.method not in self._methods:
            raise cherrypy.HTTPError(405)

        path = self.args2path(args)
        if cherrypy.request.method == "GET" and \
                self.check_permission(cherrypy.request.method):
            return self.default_get(path, kwargs)
        elif cherrypy.request.method == "OPTIONS":
            return " ".join(self._methods)

        self.kwargs = kwargs

        if cherrypy.request.method == "PUT" and \
                self.check_permission(cherrypy.request.method):
            return self.default_put(path, kwargs)
        elif cherrypy.request.method == "DELETE" and \
                self.check_permission(cherrypy.request.method):
            return self.default_delete(path, kwargs)
        elif cherrypy.request.method == "POST" and \
                self.check_permission(cherrypy.request.method):
            return self.default_post(path, kwargs)

        # No hemos pillado el método entre los permitidos -> error 405
        raise cherrypy.HTTPError(405)

    # Función GET
    def default_get(self, path, kwargs):
        ret = {
            "error": True,
            "errmsg": "NotImplemented",
        }

        return json.dumps(ret)

    # Función PUT
    def default_put(self, path, kwargs):
        ret = {
            "error": True,
            "errmsg": "NotImplemented",
        }

        return json.dumps(ret)

    # Función DELETE
    def default_delete(self, path, kwargs):
        ret = {
            "error": True,
            "errmsg": "NotImplemented",
        }

        return json.dumps(ret)

    # Función POST
    def default_post(self, path, kwargs):
        # List and get
        ret = {
            "error": True,
            "errmsg": "NotImplemented",
        }

        return json.dumps(ret)

    @staticmethod
    def args2path(args):
        return unicode('/'.join(args))

    @staticmethod
    def path2args(path):
        return path.split('/')


class ModelRestInterface(RestInterface):
    def __init__(self):
        raise NotImplemented
        self.model = "model"
        self.session = "session"

    # Funciones de logging
    def log_put(self, ob):
        pk = self.get_pk()
        args = self.kwargs.keys()
        if pk in args:
            args.remove(self.get_pk())
        args = ', '.join(args)
        self.logger.info(u"%s crea o modifica el %s con id %s, args: %s",
                         cherrypy.session.get("login", "NO IDENTIFICADO"),
                         self.model.__name__,
                         self.get_pk_val(ob),
                         args)

    def log_delete(self, ob):
        self.logger.info(u"%s borra el %s con id %s",
                         cherrypy.session.get("login", "NO IDENTIFICADO"),
                         self.model.__name__,
                         self.get_pk_val(ob))

    def log_post(self, ob):
        args = self.kwargs.keys()
        args.remove(self.get_pk())
        args = ', '.join(args)
        self.logger.info(u"%s modifica el %s con id %s, args: %s",
                         cherrypy.session.get("login", "NO IDENTIFICADO"),
                         self.model.__name__,
                         self.get_pk_val(ob),
                         args)

    # Obtención y manipulación de la pk
    def check_pk_syntax(self, pk):
        """Comprueba la sintaxis de la columna marcada com pk"""
        return True

    def get_pk(self):
        """Obtiene el campo "clave primaria" del modelo que estamos exportando
        por REST"""
        pk = self.model.mapper.primary_key[0].key

        return pk

    def get_pk_val(self, o):
        """Obtiene el valor de la clave primaria de la instancia del modelo que
        estamos exportando por REST"""
        return getattr(o, self.get_pk())

    # Obtención de los atributos del objeto
    def get_columns(self):
        """Obtiene la lista de columnas del modelo que estamos exportando por
        REST"""
        cols = []
        for col in self.model.mapper.columns:
            cols.append(col.key)

        return cols

    def get_extra_cols(self, ob):
        """Funcion para que los hijos de la clase implementen metodos
        especiales de extracción de atributos"""
        return {}

    # Argumentos para búsquedas
    def process_args(self, query, kwargs):
        """Funcion para que los hijos de la clases implementen métodos
        especiales para generar la query"""

        return query.filter_by(**kwargs)

    # Función GET
    def default_get(self, path, kwargs):

        # List and get
        ret = {}
        if len(path) == 0:
            query = self.model.query
            limit = 10  # Para que no se vaya de madre esto.
            offset = False
            if 'l' in kwargs:
                limit = int(kwargs['l'])
                del(kwargs['l'])
            if 'o' in kwargs:
                offset = int(kwargs['o'])
                del(kwargs['o'])
            if 'q' in kwargs:
                search = unicode(kwargs['q'])
                column = getattr(self.model, self.get_pk())
                query = query.filter(column.like(u"%%%s%%" % search))
                del(kwargs['q'])
            if 'a' in kwargs:
                del(kwargs['a'])
                full_content = True
                ret = []
            else:
                full_content = False

            query = self.process_args(query, kwargs)

            query = self.order_by(query)

            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)

            for ob in query.all():
                if full_content:
                    ob_dict = ob.to_dict()
                    ob_dict.update(self.get_extra_cols(ob))
                    ret.append(ob_dict)
                else:
                    pk_val = self.get_pk_val(ob)
                    ret[pk_val] = {}
                    ret[pk_val]['url'] = cherrypy.url("/%s" % pk_val)
        else:
            ob = self.model.get(path)
            if ob:
                ret = ob.to_dict()
                ret.update(self.get_extra_cols(ob))
            else:
                raise cherrypy.HTTPError(404)

        return json.dumps(ret)

    def order_by(self, query):
        """Ordenación en GET"""
        return query.order_by(self.get_pk())

    # Manipulación de atributos en put
    def put_extra_cols(self, ob, kwargs):
        return ob

    # Crea una pk si es necesario. Si es None no se crea pk (la crea el modelo)
    def create_pk(self, kwargs):
        return None

    # Lista de campos que no se actualizan aunque vengan en la entrada del put
    no_update_fields = []

    # Función PUT
    def default_put(self, path, kwargs):
        # Replace
        ret = {
            "error": False,
        }

        if len(kwargs) == 0:
            self.kwargs = kwargs = json.loads(cherrypy.request.body.read())

        try:
            pk = self.get_pk()
            # Si no viene la pk, hay que crearla!
            if not kwargs.get(pk, None):
                pk_val = self.create_pk(kwargs)
                if pk_val:
                    kwargs[pk] = pk_val

            if not self.check_pk_syntax(kwargs[pk]):
                raise Exception(self.post_err_pk if self.post_err_pk
                                else "Nombre de objeto incorrecto")

            ob = self.model.get(path)
            if not ob:
                cherrypy.response.status = "201 Creado objeto %s" % kwargs[pk]
                ob = self.model()
            setattr(ob, pk, kwargs[pk])

            for col in self.get_columns():
                if col in self.no_update_fields:
                    # Los campos listados en no_update_fields no se actualizan
                    continue
                if col in kwargs:
                    setattr(ob, col, kwargs[col])

            ob = self.put_extra_cols(ob, kwargs)

            self.log_put(ob)
            self.session.commit()

            ret = ob.to_dict()

        # except Exception, e:
        except Exception, e:
            import traceback
            self.session.rollback()
            tb = traceback.format_exc()
            cherrypy.log("Excepcion (PUT): %s; %s" % (e, tb))
            ret["error"] = True
            ret["errmsg"] = "Fallo creando el objeto: %s" % e
            raise cherrypy.HTTPError(400, "Fallo creando el objeto: %s" % e)

        return json.dumps(ret)

    # Función DELETE
    def default_delete(self, path, kwargs):
        ret = {
            "error": False,
        }

        try:
            ob = self.model.get(path)
            ob.delete()
            self.session.commit()
        except sqlalchemy.orm.exc.NoResultFound:
            raise cherrypy.HTTPError(404)

        self.log_delete(ob)
        return json.dumps(ret)

    post_err_pk = False
    post_err_col = False

    # Función POST
    def default_post(self, path, kwargs):
        # List and get
        ret = {
            "error": False,
        }

        pk = self.get_pk()
        try:
            if len(path) != 0:
                ret["error"] = True
                ret["errmsg"] = "Method not implemented"
                return json.dumps(ret)

            if not self.check_pk_syntax(kwargs[pk]):
                ret["error"] = True
                ret["errmsg"] = self.post_err_pk if self.post_err_pk \
                    else "Error en el nombre del objeto"
                return json.dumps(ret)

            if not self.post_err_col:
                self.post_err_col = {}
                for col in self.get_columns():
                    self.post_err_col[col] = \
                        "No ha introducido el campo %s" % col

            ob = self.model()
            setattr(ob, pk, kwargs[pk])
            for k, v in self.post_err_col.iteritems():
                if not kwargs.get(k, False):
                    ret = {
                        "error": True,
                        "errmsg": v,
                    }
                    return json.dumps(ret)

                setattr(ob, k, kwargs[k])
            self.put_extra_cols(ob, kwargs)

            self.session.commit()
            ret["uri"] = cherrypy.url(self.get_pk_val(ob))

        except Exception, e:
            self.session.rollback()
            cherrypy.log("Excepcion (POST): %s" % e)
            raise e
            ret["error"] = True
            ret["errmsg"] = "Fallo creando el objeto"

        self.log_post(ob)
        return json.dumps(ret)


class RestQueryInterface(RestInterface):
    _methods = ["GET", "OPTIONS"]

    # Función GET
    def default_get(self, path, kwargs):

        # List and get
        ret = []
        query = self.base_query
        limit = 10  # Para que no se vaya de madre esto.
        offset = False
        if 'l' in kwargs:
            limit = int(kwargs['l'])
            del(kwargs['l'])
        if 'o' in kwargs:
            offset = int(kwargs['o'])
            del(kwargs['o'])

        query = self.process_args(query, kwargs)

        query = self.order_by(query)

        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        for ob in query.all():
            ret.append(ob)

        return json.dumps(ret)

    def order_by(self, query):
        """Ordenación en GET"""
        # return query.order_by(self.get_pk())
        return query

    # Argumentos para búsquedas
    def process_args(self, query, kwargs):
        """Funcion para que los hijos de la clases implementen métodos
        especiales para generar la query"""

        return query.filter_by(**kwargs)

conf = {
    '/': {
        'tools.response_headers.on': True,
        'tools.response_headers.headers': [
            ('Expires', 'Sun, 19 Nov 1985 05:00:00 GMT'),
            ('Cache-Control', 'no-store, no-cache, must-revalidate, " +\
             "post-check=0, pre-check=0'),
            ('Pragma', 'no-cache')],
    }
}
