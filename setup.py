from distutils.core import setup

setup(
    name='django-ewiz',
    version='1.1.11',
    author='Alex Kavanaugh',
    author_email='kavanaugh.development@outlook.com',
    packages=['django_ewiz', 'django_ewiz/djangotoolbox', 'django_ewiz/djangotoolbox/db'],
    url='https://bitbucket.org/alex_kavanaugh/django-ewiz/',
    license='GNU LGPL',
    description="A non-relational Django database backend that utilizes EnterpriseWizard's REST interface.",
    long_description=open('README.txt').read(),
    install_requires=[
        "Django>=1.5.2",
    ],
)
