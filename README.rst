django-ewiz
%%%%%%%%%%%

A non-relational Django database backend that utilizes EnterpriseWizard's REST interface.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:Version:           1.1.20
:Dependencies:      Python 2.7, Django 1.5.2+
:Home page:         https://bitbucket.org/alex_kavanaugh/django-ewiz
:Author:            Alex Kavanaugh <kavanaugh.development@outlook.com>
:License:           GNU LGPL (http://www.gnu.org/licenses/lgpl.html)


Installation
============

Run ``pip install django-ewiz``

Add *django_ewiz* to ``INSTALLED_APPS``

.. code:: python

    INSTALLED_APPS = (
        ...
        'django_ewiz',
        ...
    )

Usage
============

Basic Usage
-----------

In the ``DATABASES`` settings dictionary, simply use *django_ewiz* as the ENGINE key.

.. code:: python

    'default': {
        'ENGINE': 'django_ewiz',
        'NAME': '',  # The name of the knowlegebase
        'USER': '',  # The name of the user
        'PASSWORD': '',  # The user's password
        'HOST': '',  # EnterpriseWizard's REST base url, generally 'www.example.com/ewws/'. Don't include the protocol string (e.g. 'http://').
        'PORT': '',  # Either 80 or 443 (HTTP or HTTPS requests only)
    },

That's it! All database operations performed will be abstracted and should function as the usual engines do (unless what you wish to do conflicts with the options below).


*The following query operations are supported:*

* exact
* iexact
* contains
* icontains
* regex
* iregex
* gt
* gte
* lt
* lte
* startswith
* endswith
* istartswith
* iendswith

*NOTE:* Not all ticket fields can be changed via REST. Add ``editable=False`` as a model option to remove DatabaseErrors.


Related Fields
--------------

EnterpriseWizard supports foreign table relationships in it's REST API. To mark a field as related, simply add ``help_text=':'`` as a model field option.

.. code:: python

    requestor_username = CharField(help_text=':', db_column='submitter_username')

Surprisingly many fields are related fields. If a DatabaseError is raised and you aren't sure why, try making the field related.


File Uploads
------------

django-ewiz does support file uploads - just not in a direct manner (binary uploads to the file field won't work [more research on abstracting that will be done later])

To mark a field as a file field, add ``help_text='file'`` as a model field option. Since trying to modify the field directly won't work, adding ``editable=False`` is recommended to avoid confusion.

.. code:: python

    file_field = CharField(help_text='file', editable=False, db_column='attached_files')

To upload a file, use the provided EwizAttacher class (``from django_ewiz import EwizAttacher``) with the following parameters:

* `settingsDict` - the DATABASES dictionary that contains ewiz connection settings. e.g. settings.DATABASES['default']
* `model` - the model instance  to which a file should be uploaded (the model must include one and only one file field). e.g. models.AccountRequest.objects.get(ticket_id = 1)
* `file_reference` - a Python file object. If the file is coming from a django form, grab it via request.FILES['form_field_name'].file
* `file_name` - the desired file name. If the file is coming from a django form, you can grab its name via request.FILES['form_field_name'].name


File Upload Example
===================


`forms.py`

.. code:: python

    from django.forms import Form, FileField
    
    class EwizUploadForm(Form):
        uploaded_file = FileField(required=True)


`models.py`

.. code:: python

    from django.db.models import Model, AutoField, CharField
    
    class AccountRequest(Model):
        ticket_id = AutoField(primary_key=True, db_column='id')
        subject_username = CharField(help_text=':')
        
        # Use this field only in conjunction with EwizAttacher - do not attempt to directly populate it
        file_field = CharField(help_text='file', editable=False, db_column='attached_files')
        
        class Meta:
            db_table = u'account_request'
            managed = False
            verbose_name = u'Account Request'

`views.py`

.. code:: python

    from django.conf import settings
    from django.views.generic.edit import FormView
    
    from django_ewiz import EwizAttacher
    
    from .forms import EwizUploadForm
    from .models import AccountRequest
    
    class UploadDemoView(FormView):
        template_name = "ewizdemo.html"
        form_class = EwizUploadForm
    
        def form_valid(self, form):
            # Create a new account request
            ticket = AccountRequest(subject_username=self.request.user.username)
            ticket.save()
    
            # Grab the file
            file_reference = self.request.FILES['uploaded_file'].file
    
            # Upload the file
            EwizAttacher(settings_dict=settings.DATABASES['default'], model=ticket, file_reference=file_reference, file_name=self.request.user.username + u'.pdf').attach_file()
