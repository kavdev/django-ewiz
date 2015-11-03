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

import logging
import re

from django.db.utils import DatabaseError
from django.utils.encoding import smart_str
import requests

from .urlbuilders import Read


# Python 2 compatibility
try:
    from urllib import unquote
except ImportError:
    from urllib.parse import unquote
try:
    from concurrent.futures import ThreadPoolExecutor
    threading = True
except ImportError:
    threading = False


logging.getLogger("django_ewiz")


class EwizDecompiler(object):
    """

    Ewiz results decompiler

    Send requests to the EnterpriseWizard database via the REST API and parses the response.

    """

    def __init__(self, model, settings_dict):
        self.model = model
        self.settings_dict = settings_dict

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
        except requests.exceptions.HTTPError as message:
            message = str(message)

            if "Error executing query, please consult logs" in message:
                message = message + ".\n\tThe query submitted most likely contains invalid or illegal syntax:\n\t %s" % unquote(url.split("&$lang=")[-1][2:])

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
            first_line = next(response.iter_lines(decode_unicode=True))
            count = pattern.match(smart_str(first_line)).group('value')

            return count, response_list
        else:
            response_lines = []

            for line in response.iter_lines(decode_unicode=True):
                response_lines.append(pattern.match(smart_str(line)).group('value'))

            count = int(response_lines[0])
            id_list = response_lines[1:]

            def read_ticket(ticket_id):
                response_url = Read(self.settings_dict, self.model._meta.db_table, ticket_id).build()
                return self.__request_single(response_url)

            num_connections = self.settings_dict.get('NUM_CONNECTIONS')
            if threading and num_connections:
                with ThreadPoolExecutor(num_connections) as pool:
                    response_list = pool.map(read_ticket, id_list)
            else:
                response_list = map(read_ticket, id_list)

        return count, response_list

    def __request_single(self, url):
        """Generates a response for a single ticket."""

        return self.__attempt_request(url)

    def __decompile(self, response):
        """Parses a response into a field, value dictionary."""

        data_list = []
        for line in response.iter_lines(decode_unicode=True):
            data_list.append(smart_str(line))

        pattern = re.compile(r"^EWREST_(?P<key>.*?)='(?P<value>.*)';$", re.DOTALL)

        data_dict = {}
        for data in data_list:
            match = pattern.match(data)
            data_dict[match.group('key')] = match.group('value')

        return data_dict
