from distutils.core import setup

setup(
    name='django-ewiz',
    version='1.3.1',
    author='Alex Kavanaugh',
    author_email='kavanaugh.development@outlook.com',
    packages=['django_ewiz'],
    url='https://bitbucket.org/kavanaugh_development/django-ewiz/',
    license='GNU LGPL (http://www.gnu.org/licenses/lgpl.html)',
    description="A non-relational Django database backend that utilizes EnterpriseWizard's REST interface.",
    long_description=open('README.rst').read(),
    install_requires=[
        "Django>=1.5",
        "djangotoolbox>=1.6.2",
        "requests>=2.3.0",
    ],
)
