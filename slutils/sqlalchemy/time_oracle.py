# -*- coding: utf-8 -*-
# Tipo especial para encapsular un time en oracle

import sqlalchemy.types as types
import logging
import datetime
zerodate = datetime.date(1, 1, 1)

logger = logging.getLogger("PTDeploy.time_oracle")


class DateTimeTime(types.TypeDecorator):
    """Encapsula un objeto time en un datetime, especial para Oracle"""

    impl = types.DateTime

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        else:
            return datetime.datetime.combine(zerodate, value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return value.time()
