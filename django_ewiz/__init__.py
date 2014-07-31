"""

django-ewiz v1 - A Non-Relational REST Django database backend for the EnterpriseWizard Service Request System.

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

from .attacher import EwizAttacher

#
# Version Classification
# Major Updates, Minor Updates, Revision/Bugfix Updates
#
VERSION = ("1", "3", "0")
__version__ = ".".join(VERSION)
