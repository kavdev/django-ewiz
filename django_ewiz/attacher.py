"""

.. module:: django-ewiz.attacher
    :synopsis: django-ewiz file attacher. Uploads files to the EnterpriseWizard database using the REST API.

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

import requests

from .urlbuilders import Attach


class EwizAttacher(object):
    """Uploads an attachment to the EnterpriseWizard database.

    NOTE:
    1) The EnterpriseWizard ticket ID must be the primary key of the passed model.

    """

    def __init__(self, settings_dict, model, file_reference, file_name):
        self.settings_dict = settings_dict
        self.table = model._meta.db_table
        self.ticket_id = model.pk
        self.file = file_reference
        self.file_name = file_name

        for field in model._meta.fields:
            if field.help_text == 'file':
                self.field_name = field.column

        if not self.field_name:
            raise model.DoesNotExist("The file field for this model does not exist.")

    def build_url(self):
        """Builds the attach REST url."""

        self.url = Attach(self.settings_dict, self.table, self.ticket_id, self.field_name, self.file_name).build()

    def attach_file(self):
        """Sends the upload request to the ewiz server."""

        self.build_url()

        response = requests.put(url=self.url, data=self.file.read(), headers={'Content-Type': 'application/octet-stream'})

        # Close the file stream
        self.file.close()

        return response
