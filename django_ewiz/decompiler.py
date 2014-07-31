from __future__ import unicode_literals

"""

.. module:: django-ewiz.decompiler
    :synopsis: django-ewiz database backend decompiler.

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

import re
import urllib
from functools import wraps

from django.db.utils import DatabaseError

import requests

from .urlbuilders import Read


def safe_call(func):
    """Function wrapper for debugging - taken from Django-Nonrel/djangotoolbox."""

    @wraps(func)
    def _func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception, message:
            raise DatabaseError(unicode(str(message)))

    return _func


class EwizDecompiler(object):
    """

    Ewiz results decompiler

    Send requests to the EnterpriseWizard database via the REST API and parses the response.

    """

    def __init__(self, model, settings_dict):
        self.model = model
        self.settings_dict = settings_dict

    @safe_call
    def decompile(self, url):
        """

        Requests tickets given a query url and parses each result.

        This method returns a list of field, value dictionaries. Each dictionary represents a ticket.

        """

        count, response_list = self.__request_multiple(url)
        query_list = []

        for response in response_list:
            query_list.append(self.__decompile(response))

        return query_list

    @safe_call
    def count(self, url):
        """

        Requests tickets given a query url and parses only the ticket count.

        This method returns the number of tickets the given query returned.

        """

        count, response_list = self.__request_multiple(url, count_only=True)

        return count

    def __attempt_request(self, url):
        """

        Attempts to submit a request to the server via its REST interface.

        :param url: The url to send a request.
        :type url: str
        :returns: The server's response.
        :raises: DatabaseError if the request fails.

        """

        response = requests.get(url)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError, message:
            message = unicode(str(message))

            if "Error executing query, please consult logs" in message:
                message = message + ".\n\tThe query submitted most likely contains invalid or illegal syntax:\n\t %s" % urllib.unquote(url.split("&$lang=")[-1][2:])

            raise DatabaseError("An error occured while attempting to query the database:\n\t" + message)

        return response

    def __request_multiple(self, url, count_only=False):
        """

        Parses a multiple ticket response into a list of responses (one for each ticket) and a count the number of tickets returned.

        Returns either the list of ticket responses or the count of tickets returned, depending on countOnly's value.

        """

        response = self.__attempt_request(url)

        pattern = re.compile(r"^EWREST_id_.* = '(?P<value>.*)';$", re.DOTALL)

        response_list = []

        # Return only the count before the heavy lifting if countOnly is True
        if count_only:
            first_line = response.iter_lines(decode_unicode=True).next()
            count = pattern.match(first_line).group('value')

            return count, response_list
        else:
            id_list = []

            for line in response.iter_lines(decode_unicode=True):
                id_list.append(pattern.match(line).group('value'))

            count = int(id_list[0])
            idList = id_list[1:]

            for ticket_id in idList:
                response_url = Read(self.settings_dict, self.model._meta.db_table, ticket_id).build()
                response_list.append(self.__request_single(response_url))

        return count, response_list

    def __request_single(self, url):
        """Generates a response for a single ticket."""

        return self.__attempt_request(url)

    def __decompile(self, response):
        """Parses a response into a field, value dictionary."""

        data_list = []
        for line in response.iter_lines(decode_unicode=True):
            data_list.append(line)

        pattern = re.compile(r"^EWREST_(?P<key>.*?)='(?P<value>.*)';$", re.DOTALL)

        data_dict = {}
        for data in data_list:
            match = pattern.match(data)
            data_dict[match.group('key')] = match.group('value')

        return data_dict
