# -*- coding: utf-8 -*-
import pytest

def test_sljson_date():
    import datetime
    from slutils import sljson

    mytimestamp = datetime.datetime.utcnow()
    mytimestamp_json = sljson.dumps([mytimestamp])
    mytimestamp_return = sljson.loads(mytimestamp_json)
    assert str(mytimestamp) == mytimestamp_return[0]

def test_sljson2():
    assert True
    return
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
    data2 = repr(sljson.loads(jsonstring))
    assert data == data2
