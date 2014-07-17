import logging
import logging.config
import cherrypy
import os


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


class StdFormatter(logging.Formatter):
    def format(self, record):
        record.msg = "%s - %s" % \
            (cherrypy.request.remote.name or cherrypy.request.remote.ip,
             record.msg)
        return logging.Formatter.format(self, record)

MSG_FORMAT = "%(asctime)s - %(message)s"
DATE_FORMAT = "[%d/%b/%Y:%H:%M:%S]"


def configLogFromFile(cfile):
    if not os.path.isfile(cfile):
        cfile = os.path.join(os.path.dirname(__file__), "conf", cfile)

    logging.config.fileConfig(cfile, disable_existing_loggers=False)


def loggerForModule(module_name):
    logger = logging.getLogger(module_name)
    return logger


def disableLogging(module_name):
    logger = loggerForModule(module_name)
    logger.addHandler(NullHandler())

    return logger


class LogErrors(cherrypy.Tool):
    _name = 'LogError'
    _priority = 10
    _point = 'after_error_response'

    def __init__(self):
        pass

    def callable(self, logger_name="critical_errors", errors=None, **kwargs):
        self.logger = logging.getLogger(logger_name)
        self.errors = errors

        s = "status: %s;" % cherrypy.response.status
        s += "request_line: %s;" % cherrypy.request.request_line
        s += "params: %s;" % str(cherrypy.request.params)
        s += "exc: %s" % cherrypy._cperror.format_exc(exc=None)
        self.logger.debug("%s", s)

cherrypy.tools.LogErrors = LogErrors()
