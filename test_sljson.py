# -*- coding: utf-8 -*-
import pytest

def test_sljson():
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
    data2 = repr(sljson.loads(jsonstring))
    assert data == data2
