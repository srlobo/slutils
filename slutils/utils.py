# -*- coding: utf-8 -*-
# Utilidades varias (toolbox)


def synchronized(lock):
    """ Synchronization decorator.
    Usage:
        import threading
        lock = threading.Lock()
        @synchronized(lock)
        def function():
            something synchronous

        """
    def wrap(f):
        def newFunction(*args, **kw):
            with lock:
                return f(*args, **kw)
        return newFunction
    return wrap
