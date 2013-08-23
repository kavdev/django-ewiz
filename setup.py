from distutils.core import setup

setup(
    name='django-ewiz',
    version='1.1.9',
    author='Alex Kavanaugh',
    author_email='kavanaugh.development@outlook.com',
    packages=['django_ewiz'],
    url='http://pypi.python.org/pypi/django-ewiz/',
    license='GNU LGPL',
    description="A non-relational Django database backend that utilizes EnterpriseWizard's REST interface.",
    long_description=open('README.txt').read(),
    dependency_links = ['https://github.com/django-nonrel/djangotoolbox.git@toolbox-1.4#egg=djangotoolbox'],
    install_requires=[
        "Django>=1.5.2",
    ],
)
