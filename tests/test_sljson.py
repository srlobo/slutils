# -*- coding: utf-8 -*-
import pytest

def test_sljson_date():
    import datetime
    from slutils import sljson

    mytimestamp = datetime.datetime.utcnow()
    mytimestamp_json = sljson.dumps({'ts': mytimestamp})
    mytimestamp_return = sljson.loads(mytimestamp_json)
    assert mytimestamp == mytimestamp_return['ts']

def test_sljson2():
    import datetime
    from slutils import sljson

    mytimestamp = datetime.datetime.utcnow()
    mydate = datetime.date.today()
    data = dict(
        foo=42,
        bar=[mytimestamp, mydate],
        date=mydate,
        timestamp=mytimestamp,
        struct=dict(
            date2=mydate,
            timestamp2=mytimestamp
        )
    )

    jsonstring = sljson.dumps(data)
    data2 = sljson.loads(jsonstring)
    k = data.keys()
    k.sort()
    k2 = data2.keys()
    k2.sort()
    assert k == k2
    assert data == data2
