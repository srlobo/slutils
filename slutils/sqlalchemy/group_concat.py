# -*- coding: utf-8 -*-
# Añade la funcionalidad group_concat de mysql al sqlalchemy
from sqlalchemy.ext import compiler
from sqlalchemy.sql import ColumnElement
from sqlalchemy.orm.attributes import InstrumentedAttribute


class group_concat(ColumnElement):
    def __init__(self, col1, col2=None, separator=None):
        if isinstance(col1, InstrumentedAttribute):
            self.col1 = col1.property.columns[0]
        else:
            self.col1 = col1

        if col2 is not None:
            if isinstance(col2, InstrumentedAttribute):
                self.col2 = col2.property.columns[0]
            else:
                self.col2 = col2
        else:
            self.col2 = self.col1

        self.type = self.col1.type

        self.separator = separator


@compiler.compiles(group_concat, 'mysql')
def compile_group_concat(element, compiler, **kw):
    if element.separator:
        return "GROUP_CONCAT(%s ORDER BY %s SEPARATOR '%s')" % (
            compiler.process(element.col1),
            compiler.process(element.col2),
            element.separator,
        )
    else:
        return "GROUP_CONCAT(%s ORDER BY %s)" % (
            compiler.process(element.col1),
            compiler.process(element.col2),
        )


if __name__ == "__main__":

    from sqlalchemy import MetaData, Table, Column, String, select
    from sqlalchemy import create_engine

    m = MetaData()
    t = Table('t1', m, Column('foo', String), Column('bar', String))

    print select([group_concat(t.c.foo, t.c.bar)]).\
        compile(bind=create_engine('mysql://'))

    print select([group_concat(t.c.foo)]).\
        compile(bind=create_engine('mysql://'))

    print select([group_concat(t.c.foo, separator="tocata")]).\
        compile(bind=create_engine('mysql://'))
