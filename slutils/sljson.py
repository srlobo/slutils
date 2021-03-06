# -*- coding: utf-8 -*-
# Sacado de:
# http://stackoverflow.com/questions/455580/json-datetime-between-python-and-javascript
# Un codec json que atiende a fechas en formato "normal"

__all__ = ['dumps', 'loads']

import datetime
import elixir

try:
    import json
except ImportError:
    import simplejson as json


class JSONDateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime, datetime.time)):
            return obj.isoformat()
        if isinstance(obj, elixir.Entity):
            return obj.to_dict()
        else:
            return json.JSONEncoder.default(self, obj)


def datetime_decoder(d):
    if isinstance(d, list):
        pairs = enumerate(d)
    elif isinstance(d, dict):
        pairs = d.items()
    result = []
    for k, v in pairs:
        if isinstance(v, basestring):
            try:
                # The %f format code is only supported in Python >= 2.6.
                # For Python <= 2.5 strip off microseconds
                # v = datetime.datetime.strptime(v.rsplit('.', 1)[0],
                #     '%Y-%m-%dT%H:%M:%S')
                v = datetime.datetime.strptime(v, '%Y-%m-%dT%H:%M:%S.%f')
            except ValueError:
                try:
                    v = datetime.datetime.strptime(v, '%Y-%m-%d').date()
                except ValueError:
                    pass
        elif isinstance(v, (dict, list)):
            v = datetime_decoder(v)
        result.append((k, v))
    if isinstance(d, list):
        return [x[1] for x in result]
    elif isinstance(d, dict):
        return dict(result)


def dumps(obj):
    return json.dumps(obj, cls=JSONDateTimeEncoder)


def loads(obj):
    return json.loads(obj, object_hook=datetime_decoder)
