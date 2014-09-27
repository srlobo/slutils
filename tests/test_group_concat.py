# -*- coding: utf-8 -*-
from sqlalchemy import MetaData, Table, Column, String, select
from sqlalchemy import create_engine
from slutils.sqlalchemy.group_concat import group_concat

m = MetaData()
t = Table('t1', m, Column('foo', String), Column('bar', String))

s = select([group_concat(t.c.foo, t.c.bar)]).\
    compile(bind=create_engine('mysql://')) != ""

assert s != ""

s = select([group_concat(t.c.foo)]).\
    compile(bind=create_engine('mysql://'))

assert s != ""

s = select([group_concat(t.c.foo, separator="tocata")]).\
    compile(bind=create_engine('mysql://'))

assert s != ""
