# -*- coding: utf-8 -*-
# $Id$

import sqlalchemy.types as types
import logging

logger = logging.getLogger("slutils.sqlalchemy.sqlalchemy_ip")


class IpAddress(types.TypeDecorator):
    """Encapsula una dirección ip en un entero"""

    impl = types.BigInteger

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        else:
            return inet_atoi(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return inet_itoa(value)


class IpMask(IpAddress):
    """Encapsula una máscara ipv4 en un entero"""
    pass


def inet_atoi(ip_a):
    """Transforma una ip del formato de 4 bytes separados por . a un entero de
    32bits."""

    try:
        ip_a = int(ip_a)
        return ip_a
    except:
        pass

    try:
        ip_a = ip_a.split('.')

        ip_i = 0
        ip_i += int(ip_a[0]) << 24
        ip_i += int(ip_a[1]) << 16
        ip_i += int(ip_a[2]) << 8
        ip_i += int(ip_a[3])
    except:
        if type(ip_a) != int:
            raise TypeError("La cadena %s no es una dirección IPv4 válida"
                            % ip_a)
        if int(ip_a) > 0 and int(ip_a) <= 4294967295:
            ip_i = ip_a
        else:
            raise TypeError("La cadena %s no es una dirección IPv4 válida"
                            % ip_a)
    return ip_i


def inet_itoa(ip_i):
    """Transforma una ip de un entero de 32bits al formato de 4 bytes separados
    por ."""

    try:
        ip_i = int(ip_i)
        ip_a = []
        ip_a.append((inet_atoi("255.0.0.0") & ip_i) >> 24)
        ip_a.append((inet_atoi("0.255.0.0") & ip_i) >> 16)
        ip_a.append((inet_atoi("0.0.255.0") & ip_i) >> 8)
        ip_a.append((inet_atoi("0.0.0.255") & ip_i))

        ip_a = map(lambda x: "%d" % x, ip_a)
        logger.debug("%s -> %s", ip_i, ip_a)
    except:
        raise TypeError("El entero no representa una dirección IPv4 válida")

    return ".".join(ip_a)
