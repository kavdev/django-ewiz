"""

.. module:: django-ewiz.compiler
    :synopsis: django-ewiz database backend compilers.

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
import re
import urllib2
from functools import wraps

from django.db.utils import DatabaseError, IntegrityError
from django.db.models.sql.constants import SINGLE, MULTI
from django.db.models.sql import aggregates as sqlaggregates
from django.utils.datastructures import SortedDict

from .djangotoolbox.db.basecompiler import (NonrelQuery, NonrelCompiler, NonrelInsertCompiler, NonrelUpdateCompiler, NonrelDeleteCompiler)

from .decompiler import EwizDecompiler
from .urlbuilders import Select, Update, Insert


def safe_call(func):
    """Function wrapper for debugging - taken from Django-Nonrel/djangotoolbox."""

    @wraps(func)
    def _func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception, message:
            raise DatabaseError(str(message) + str(sys.exc_info()[2]))

    return _func


class EwizQuery(NonrelQuery):
    """

    The Ewiz class layer for nonrel queries.

    This class provides the framework for a query to the Ewiz REST interface.

    """

    # A dictionary of operators and their ewiz REST representations.
    operators = {
        'exact': lambda lookup_type, value: (u"= BINARY", u"'" + unicode(str(value)) + u"'"),
        'iexact': lambda lookup_type, value: (u"=", u"'" + unicode(str(value)) + u"'"),
        'contains': lambda lookup_type, value: (u"LIKE BINARY", u"'%" + unicode(str(value)) + u"%'"),
        'icontains': lambda lookup_type, value: (u"LIKE", u"'%" + unicode(str(value)) + u"%'"),
        'gt': lambda lookup_type, value: (u">", u"'" + unicode(str(value)) + u"'"),
        'gte': lambda lookup_type, value: (u">=", u"'" + unicode(str(value)) + u"'"),
        'lt': lambda lookup_type, value: (u"<", u"'" + unicode(str(value)) + u"'"),
        'lte': lambda lookup_type, value: (u"<=", u"'" + unicode(str(value)) + u"'"),
        'in': lambda lookup_type, value: (u"IN", value),
        'startswith': lambda lookup_type, value: (u"LIKE BINARY", u"'" + unicode(str(value)) + u"%'"),
        'istartswith': lambda lookup_type, value: (u"LIKE", u"'" + unicode(str(value)) + u"%'"),
        'endswith': lambda lookup_type, value: (u"LIKE BINARY", u"'%" + unicode(str(value)) + u"'"),
        'iendswith': lambda lookup_type, value: (u"LIKE", u"'%" + unicode(str(value)) + u"'"),
        'range': lambda lookup_type, value: (u"BETWEEN", unicode(str(value))),
        'isnull': lambda lookup_type, value: (u"IS NULL", None),
        'regex': lambda lookup_type, value: (u"REGEXP BINARY", u"'" + unicode(str(value)) + u"'"),
        'iregex': lambda lookup_type, value: (u"REGEXP", u"'" + unicode(str(value)) + u"'"),
    }

    # A dictionary of operators and their negated ewiz REST representations.
    negated_operators = {
        'exact': lambda lookup_type, value: (u"!= BINARY", u"'" + unicode(str(value)) + u"'"),
        'iexact': lambda lookup_type, value: (u"!=", u"'" + unicode(str(value)) + u"'"),
        'contains': lambda lookup_type, value: (u"NOT LIKE BINARY", u"'%" + unicode(str(value)) + u"%'"),
        'icontains': lambda lookup_type, value: (u"NOT LIKE", u"'%" + unicode(str(value)) + u"%'"),
        'gt': lambda lookup_type, value: (u"<", u"'" + unicode(str(value)) + u"'"),
        'gte': lambda lookup_type, value: (u"<=", u"'" + unicode(str(value)) + u"'"),
        'lt': lambda lookup_type, value: (u">", u"'" + unicode(str(value)) + u"'"),
        'lte': lambda lookup_type, value: (u">=", u"'" + unicode(str(value)) + u"'"),
        'in': lambda lookup_type, value: (u"NOT IN", value),
        'startswith': lambda lookup_type, value: (u"NOT LIKE BINARY", u"'" + unicode(str(value)) + u"%'"),
        'istartswith': lambda lookup_type, value: (u"NOT LIKE", u"'" + unicode(str(value)) + u"%'"),
        'endswith': lambda lookup_type, value: (u"NOT LIKE BINARY", u"'%" + unicode(str(value)) + u"'"),
        'iendswith': lambda lookup_type, value: (u"NOT LIKE", u"'%" + unicode(str(value)) + u"'"),
        'range': lambda lookup_type, value: (u"NOT BETWEEN", unicode(str(value))),
        'isnull': lambda lookup_type, value: (u"IS NOT NULL", None),
        'regex': lambda lookup_type, value: (u"NOT REGEXP BINARY", u"'" + unicode(str(value)) + u"'"),
        'iregex': lambda lookup_type, value: (u"NOT REGEXP", u"'" + unicode(str(value)) + u"'"),
    }

    def __init__(self, compiler, fields):
        super(EwizQuery, self).__init__(compiler, fields)
        self.compiled_query = {
            'table': None,
            'filters': [],
            'ordering': [],
            'limits': {
                'offset': u'0',
                'limit': u'18446744073709551615'  # Max limit as proposed by MySQL,
            },
        }

    def __debug(self):
        return (u'DEBUG INFO:' +
            u'\n\nRAW_QUERY: ' + str(self.query) +
            u'\nCOMPILED_QUERY: ' + str(self.compiled_query) +
            u'\nQUERY_URL: ' + str(Select(self.connection.settings_dict, self.query.model._meta.db_table, self.compiled_query).build())
        )

    @safe_call
    def fetch(self, low_mark=0, high_mark=None):
        """

        EwizQueryCompiler

        Gathers query parameters (filters, ordering, etc.) into a comiledQuery dictionary,
        builds a URL using those parameters (via URL Builders),
        and uses the decompiler to pull data using the REST API.

        This method returns an iterator (using for/yield) over the query results.

        """

        # Handle all records requests
        if not self.compiled_query["filters"]:
            self.compiled_query["filters"] = [u"id LIKE '%'"]

        if high_mark is None:
            # Infinite fetching
            self.compiled_query["limits"]["offset"] = unicode(str(low_mark))
            self.compiled_query["limits"]["limit"] = u'18446744073709551615'  # Max limit as proposed by MySQL
        elif high_mark > low_mark:
            # Range fetching
            self.compiled_query["limits"]["offset"] = unicode(str(low_mark))
            self.compiled_query["limits"]["limit"] = unicode(str(high_mark - low_mark))
        else:
            # Invalid range
            self.compiled_query["limits"]["offset"] = unicode(str(0))
            self.compiled_query["limits"]["limit"] = unicode(str(0))

        # Build the url
        url = Select(self.connection.settings_dict, self.query.model._meta.db_table, self.compiled_query).build()

        # Fetch and decompiler the results
        query_results = EwizDecompiler(self.query.model, self.connection.settings_dict).decompile(url)

        # Yield each result
        for result in query_results:
            yield result

    @safe_call
    def count(self, limit=None):
        """

        EwizQueryCounter

        Sends the query to Ewiz via the REST API, but only decompiles and returns the result count.

        This method returns the number of results a query will yield.

        """

        # Pass given limit to the compiled query
        if limit:
            self.compiled_query["limits"]["limit"] = str(unicode(limit))

        # Build the url
        url = Select(self.connection.settings_dict, self.query.model._meta.db_table, self.compiled_query).build()
        # Send the query, but only fetch and decompile the result count
        count = EwizDecompiler(self.query.model, self.connection.settings_dict).count(url)

        return count

    @safe_call
    def delete(self):
        raise NotImplementedError(u"Deleting EnterpriseWizard records is generally ill-advised. Please contact your EnterpriseWizard administrator for more information.")

    @safe_call
    def order_by(self, ordering):
        """

        EwizQueryOrderer

        Adds the ORDER BY parameter to the compiled query. Default: ORDER BY id ASC.

        NOTE:
        1) EnterpriseWizard's REST interface does not correctly represent ORDER BY queries. The Ewiz
           backend handles the query fine, but the frontend reorders it by ticketID. Since this causes
           limited results to be yielded incorrectly, this feature has been disabled until further notice.

        """

        # A True/False ordering designates default ordering.
        if type(ordering) is bool:
            if ordering:
                self.compiled_query["ordering"].append(u'id ASC')
            else:
                raise DatabaseError(u"The 'ORDER BY' statement is not currently supported by the EnterpriseWizard REST interface.")
                self.compiled_query["ordering"].append(u'id DESC')
        # A list of ordering tuples designates multiple ordering (non-default)
        else:
            for order in ordering:
                field = order[0]
                if order[1]:
                    direction = u'ASC'
                else:
                    direction = u'DESC'

                self.compiled_query["ordering"].append(field.name + u' ' + direction)

            raise DatabaseError(u"The 'ORDER BY' statement is not currently supported by the EnterpriseWizard REST interface.")

    @safe_call
    def add_filter(self, field, lookup_type, negated, value):
        """

        EwizQueryFilterer

        Adds a single constraint to be used in the WHERE clause of the compiled query.

        This method is called by the add_filters method of NonrelQuery

        """

        # Determine operator
        if negated:
            try:
                operator = self.negated_operators[lookup_type]
            except KeyError:
                raise DatabaseError("Lookup type %r can't be negated" % lookup_type)
        else:
            try:
                operator = self.operators[lookup_type]
            except KeyError:
                raise DatabaseError("Lookup type %r isn't supported" % lookup_type)

        # Handle lambda lookup types
        if callable(operator):
            operator, value = operator(lookup_type, value)

        self.compiled_query["filters"].append(field.column + u' ' + operator + u' ' + value)


class EwizCompiler(NonrelCompiler):
    """

    The Ewiz Query Compiler

    This handles SELECT queries and is the base class for INSERT, and UPDATE requests.

    """

    query_class = EwizQuery

    def execute_sql(self, result_type=MULTI):
        """

        Handles SQL-like aggregate queries. This method emulates COUNT
        by using the NonrelQuery.count method.

        """

        aggregates = self.query.aggregate_select.values()

        try:
            saveCheck = self.query.extra["a"] == (u'1', [])
        except:
            pass

        # Simulate a count().
        if aggregates:
            assert len(aggregates) == 1
            aggregate = aggregates[0]
            assert isinstance(aggregate, sqlaggregates.Count)
            opts = self.query.get_meta()
            assert aggregate.col == '*' or \
                   aggregate.col == (opts.db_table, opts.pk.column)
            count = self.get_count()
            if result_type is SINGLE:
                return [count]
            elif result_type is MULTI:
                return [[count]]
        #
        # The save() method determines whether to UPDATE or INSERT based on whether or not primary_key query results exist (if a primary_key is not supplied, INSERT is chosen)
        # The following conditional section is a small hack that uses the count() method to count the number of results returned.
        #
        # False is returned if zero results are returned, True otherwise.
        #
        elif saveCheck:
            self.query.extra = SortedDict()
            count = self.get_count()
            if result_type is SINGLE:
                return (count != 0)
            elif result_type is MULTI:
                return (count != 0)

        raise NotImplementedError("The database backend only supports "
                                  "count() queries.")


class EwizInsertCompiler(NonrelInsertCompiler, EwizCompiler):
    """

    Ewiz Insert Compiler

    Creates new tickets in the Ewiz database via the REST API.

    """

    @safe_call
    def execute_sql(self, return_id=False):
        """

        Prepares field, value tuples for the compiler to use and,
        if requested, returns the primary key of the new ticket.

        """

        docs = []
        pk = self.query.get_meta().pk
        for obj in self.query.objs:
            doc = []
            for field in self.query.fields:
                value = field.get_db_prep_save(
                    getattr(obj, field.attname) if self.query.raw else field.pre_save(obj, obj._state.adding),
                    connection=self.connection
                )
                if not field.null and value is None and not field.primary_key:
                    raise IntegrityError("You can't set %s (a non-nullable "
                                         "field) to None!" % field.name)

                # Prepare value for database, note that query.values have
                # already passed through get_db_prep_save.
                value = self.ops.value_for_db(value, field)
                doc.append((field, value))

            docs.append(doc)

        if len(docs) > 1:
            raise DatabaseError(u'INSERT COMPILER: Docs length assumption was wrong. Contact Alex Kavanaugh with details./n/tDocs Length: ' + unicode(str(len(docs))))

        key = self.insert(docs[0], return_id=return_id)
        # Pass the key value through normal database deconversion.
        return self.ops.convert_values(self.ops.value_from_db(key, pk), pk)

    @safe_call
    def insert(self, values, return_id):
        """Builds and sends a query to create a new ticket in the Ewiz database."""

        # Build the url
        url = Insert(self.connection.settings_dict, self.query.model._meta.db_table, values).build()

        # Attempt the Insert
        request = urllib2.Request(url)

        try:
            response = urllib2.urlopen(request)

            # Return the new ID
            if return_id:
                pattern = re.compile(r"^EWREST_id='(?P<value>.*)';$", re.DOTALL)

                idList = []
                for line in iter(lambda: unicode(response.readline().decode('string-escape').strip(), 'ISO-8859-1'), ""):
                    idList.append(pattern.match(line).group('value'))
                return int(idList[0])

        except urllib2.HTTPError, message:
            raise DatabaseError(self.query.model._meta.object_name + u' - An INSERT error has occurred. Please contact the development team with the following details:\n\t' + unicode(str(message)))


class EwizUpdateCompiler(NonrelUpdateCompiler):
    """

    Ewiz Insert Compiler

    Creates new tickets in the Ewiz database via the REST API.

    """

    @safe_call
    def update(self, values):
        """Builds and sends a query to update/change information in a ticket that currently exists in the Ewiz database."""

        # Build the url
        try:
            ticketID = self.query.where.children[0].children[0][-1]
        except:
            raise DatabaseError(u'UPDATE COMPILER: UPDATE ticketID assumptions were wrong. Contact Alex Kavanaugh with details.')
        url = Update(self.connection.settings_dict, self.query.model._meta.db_table, ticketID, values).build()

        # Attempt the Update
        request = urllib2.Request(url)

        try:
            urllib2.urlopen(request)
        except urllib2.HTTPError, message:
            raise DatabaseError(self.query.model._meta.object_name + u' - An UPDATE error has occurred. Please contact the development team with the following details:\n\t' + unicode(str(message)))


class EwizDeleteCompiler(NonrelDeleteCompiler):

    @safe_call
    def execute_sql(self, result_type=None):
        raise NotImplementedError(u"Deleting EnterpriseWizard records is generally ill-advised. Please contact your EnterpriseWizard administrator for more information.")

# Assign new compiler classes as default compilers
SQLCompiler = EwizCompiler
SQLInsertCompiler = EwizInsertCompiler
SQLUpdateCompiler = EwizUpdateCompiler
SQLDeleteCompiler = EwizDeleteCompiler
