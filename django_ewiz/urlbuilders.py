from __future__ import unicode_literals

"""

.. module:: django-ewiz.urlbuilders
    :synopsis: django-ewiz database backend URL builders.

    django-ewiz is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    django-ewiz is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU Lesser Public License for more details.

    You should have received a copy of the GNU Lesser Public License
    along with django-ewiz. If not, see <http://www.gnu.org/licenses/>.

.. moduleauthor:: Alex Kavanaugh <kavanaugh.development@outlook.com>

"""

import sys
import urllib
import logging

from functools import wraps

from django.db.utils import DatabaseError

logger = logging.getLogger("django_ewiz_urls")


def safe_call(func):
    """Function wrapper for debugging - taken from Django-Nonrel/djangotoolbox."""

    @wraps(func)
    def _func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception, message:
            raise DatabaseError(unicode(str(message)) + unicode(str(sys.exc_info()[2])))

    return _func


class Read(object):
    """

    Builds a READ url

    Sending a READ request returns a response containing fields and values for the provided ticket ID

    """

    def __init__(self, settings_dict, table, ticket_id):
        if settings_dict["PORT"] == "443":
            self.protocol = 'https://'
        else:
            self.protocol = 'http://'

        self.host = settings_dict["HOST"]
        self.knowledge_base = settings_dict["NAME"]
        self.login = settings_dict["USER"]
        self.password = settings_dict["PASSWORD"]
        self.language = 'en'
        self.table = table
        self.ticket_id = ticket_id

    @safe_call
    def build(self):
        url = urllib.quote(self.protocol + self.host + 'EWRead?$KB=' + self.knowledge_base + '&$table=' + self.table + '&$login=' + self.login + '&$password=' + self.password + '&$lang=' + self.language + '&id=' + str(self.ticket_id), ":/?$&='")
        logger.debug(url)

        return url


class Select(object):
    """

    Builds a Select url

    Sending a SELECT request returns a response containing the number of tickets and a list of ticketIDs that adhere to the query constraints.

    """

    def __init__(self, settings_dict, table, compiled_query):
        if settings_dict["PORT"] == "443":
            self.protocol = 'https://'
        else:
            self.protocol = 'http://'

        self.host = settings_dict["HOST"]
        self.knowledge_base = settings_dict["NAME"]
        self.login = settings_dict["USER"]
        self.password = settings_dict["PASSWORD"]
        self.language = 'en'
        self.table = table
        self.compiled_query = compiled_query

    @safe_call
    def build(self):
        url = urllib.quote(self.__build_select() + self.__build_where(), ":/?$&='")
        logger.debug(url)

        return url

    def __build_select(self):
        return self.protocol + self.host + 'EWSelect?$KB=' + self.knowledge_base + '&$table=' + self.table + '&$login=' + self.login + '&$password=' + self.password + '&$lang=' + self.language

    def __build_where(self):
        # Build filters string
        filters = ''
        for query_filter in self.compiled_query["filters"][:-1]:
            filters += query_filter + ' AND '
        else:
            filters += self.compiled_query["filters"][-1]

        # Build ordering string
        ordering = ' ORDER BY '
        for order in self.compiled_query["ordering"][:-1]:
            ordering += order + ', '
        else:
            ordering += self.compiled_query["ordering"][-1]

        # Build limits string
        limit = ' LIMIT ' + self.compiled_query["limits"]["limit"]
        offset = ' OFFSET ' + self.compiled_query["limits"]["offset"]

        return '&where=' + filters + ordering + limit + offset


class Insert(object):
    """

    Builds an Insert url

    Assuming there are no errors in the request, sending an INSERT request creates a ticket
    in the EnterpriseWizard database and returns the automatically generated ticket_id.

    """

    def __init__(self, settings_dict, table, data):
        if settings_dict["PORT"] == "443":
            self.protocol = 'https://'
        else:
            self.protocol = 'http://'

        self.host = settings_dict["HOST"]
        self.knowledge_base = settings_dict["NAME"]
        self.login = settings_dict["USER"]
        self.password = settings_dict["PASSWORD"]
        self.language = 'en'
        self.table = table
        self.data = data

    @safe_call
    def build(self):
        url = urllib.quote(self.__build_insert() + self.__build_data() + '&time_spent=0:0:1:0', ":/?$&='")
        logger.debug(url)

        return url

    @safe_call
    def __build_insert(self):
        return self.protocol + self.host + 'EWCreate?$KB=' + self.knowledge_base + '&$table=' + self.table + '&$login=' + self.login + '&$password=' + self.password + '&$lang=' + self.language

    @safe_call
    def __build_data(self):
        data_string = ''
        for field, value in self.data:
            # Only insert if the field is editable and the field has a value or is allowed to be blank
            if (value or field.blank):  # field.editable and
                data_string += '&' + field.column + '=' + field.help_text + unicode(str(value))

        return data_string


class Update(object):
    """

    Builds an Update url

    Assuming there are no errors in the request, sending an UPDATE request updates/changes data
    in a ticket in the EnterpriseWizard database. Nothing is returned.

    """

    def __init__(self, settings_dict, table, ticket_id, data):
        if settings_dict["PORT"] == "443":
            self.protocol = 'https://'
        else:
            self.protocol = 'http://'

        self.host = settings_dict["HOST"]
        self.knowledge_base = settings_dict["NAME"]
        self.login = settings_dict["USER"]
        self.password = settings_dict["PASSWORD"]
        self.language = 'en'
        self.table = table
        self.ticket_id = unicode(str(ticket_id))
        self.data = data

    @safe_call
    def build(self):
        url = urllib.quote(self.__build_update() + self.__build_data() + '&time_spent=0:0:1:0', ":/?$&='")
        logger.debug(url)

        return url

    @safe_call
    def __build_update(self):
        return self.protocol + self.host + 'EWUpdate?$KB=' + self.knowledge_base + '&$table=' + self.table + '&$login=' + self.login + '&$password=' + self.password + '&$lang=' + self.language

    @safe_call
    def __build_data(self):
        data_string = '&id=' + self.ticket_id
        for field, value in self.data:
            # Only update if the field is editable and the field has a value or is allowed to be blank
            if field.editable and (value or field.blank):
                data_string += '&' + field.column + '=' + field.help_text + unicode(str(value))

        return data_string


class Attach(object):
    """

    Builds an ATTACH url

    The ATTACH request must be sent via HTTP PUT. The number of attached files is returned upon upload success.

    """

    def __init__(self, settings_dict, table, ticket_id, field_name, file_name):
        if settings_dict["PORT"] == "443":
            self.protocol = 'https://'
        else:
            self.protocol = 'http://'

        self.host = settings_dict["HOST"]
        self.knowledge_base = settings_dict["NAME"]
        self.login = settings_dict["USER"]
        self.password = settings_dict["PASSWORD"]
        self.language = 'en'
        self.table = table
        self.ticket_id = ticket_id
        self.field_name = field_name
        self.file_name = file_name

    @safe_call
    def build(self):
        url = urllib.quote(self.protocol + self.host + 'EWAttach?$KB=' + self.knowledge_base + '&$table=' + self.table + '&$login=' + self.login + '&$password=' + self.password + '&$lang=' + self.language + '&id=' + str(self.ticket_id) + '&field=' + str(self.field_name) + '&fileName=' + str(self.file_name), ":/?$&='")
        logger.debug(url)

        return url
