"""

.. module:: django-ewiz.base
    :synopsis: django-ewiz database backend base.

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

from djangotoolbox.db.base import (NonrelDatabaseFeatures, NonrelDatabaseOperations, NonrelDatabaseWrapper, NonrelDatabaseClient,
                                NonrelDatabaseValidation, NonrelDatabaseIntrospection, NonrelDatabaseCreation)


class DatabaseOperations(NonrelDatabaseOperations):
    compiler_module = __name__.rsplit('.', 1)[0] + '.compiler'


class DatabaseWrapper(NonrelDatabaseWrapper):
    operators = {
        'exact': "= '%s'",
        'iexact': "= '%s'",
        'contains': "LIKE '%%25%s%%25'",
        'icontains': "LIKE '%%25%s%%25'",
        'gt': "> '%s'",
        'gte': ">= '%s'",
        'lt': "< '%s'",
        'lte': "<= '%s'",
        'startswith': "LIKE '%s%%25'",
        'endswith': "LIKE '%%25%s'",
        'istartswith': "LIKE '%s%%25'",
        'iendswith': "LIKE '%%25%s'",
        'in': "IN (%s)",
        'range': "BETWEEN AND(%s)",
        'year': "BETWEEN AND(%s)",
        'isnull': "IS NULL",
    }

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)

        self.server_version = None
        self.features = NonrelDatabaseFeatures(self)
        self.ops = DatabaseOperations(self)
        self.client = NonrelDatabaseClient(self)
        self.creation = NonrelDatabaseCreation(self)
        self.introspection = NonrelDatabaseIntrospection(self)
        self.validation = NonrelDatabaseValidation(self)
