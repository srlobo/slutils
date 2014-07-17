#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import ldap
import ldap.sasl
import datetime
import pytz

logger = logging.getLogger("slutils.auth.ad")


def decode_sid(sid):
    """Convierte una expresión de SID binaria en la notación canónica
    recomendada por MS, es decir:
    S-<Authority>-<Subauthority1>-<Subauthority2>-.....
    """

    # sid = sid.encode("hex")
    # Revision
    res = "S-"
    res += str(int(sid[0].encode("hex"), 16))
    # SubAuthorityCount
    # res += "-"
    # res += str(int(sid[1].encode("hex"), 16))
    # IdentifierAuthority
    res += "-"
    res += str(int(sid[2:8].encode("hex"), 16))
    for subauth in range(0, int(sid[1].encode("hex"), 16)):
        begin = 4 * subauth + 7
        end = begin + 4
        res += "-"
        res += str(int(sid[end:begin:-1].encode("hex"), 16))

    return res


def encode_sid(sid):
    """Convierte una expresión de SID expresada en notación canónica en un a
    expresión en notacion binaria"""

    sid = sid.split('-')
    logger.info(str(sid))
    res = ""
    # Revision
    res += "%02X" % int(sid[1])
    # SubAuthorityCount
    res += "%02X" % int(len(sid) - 3)
    # IdentifierAuthority
    res += "%012X" % int(sid[2])
    for subauth in sid[3:]:
        tmp = "%08X" % int(subauth)
        res += tmp[6:8] + tmp[4:6] + tmp[2:4] + tmp[0:2]

    return res.decode("hex")


def interval2date(interval):
    """Convierte el tipo de dato interval de AD a una fecha"""

    # El tipo interval de AD es la cantidad de intervalos de 100 nanosegundos
    # desde el 1 de enero de 1601(UTC)
    tz = pytz.utc
    origin = datetime.datetime(1601, 1, 1, tzinfo=tz)
    # Pasamos el número a segundos
    seconds = int(interval) * pow(10, -7)
    delta = datetime.timedelta(seconds=seconds)

    dst = origin + delta

    return dst.astimezone(pytz.timezone("CET"))
