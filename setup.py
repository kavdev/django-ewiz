import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='django-ewiz',
    version='1.5.4',
    author='Alex Kavanaugh',
    author_email='kavanaugh.development@outlook.com',
    description="A non-relational Django database backend that utilizes EnterpriseWizard's REST interface.",
    long_description=read('README.rst'),
    keywords="django ewiz enterprise wizard srs",
    license='GNU LGPL (http://www.gnu.org/licenses/lgpl.html)',
    url='https://github.com/kavdev/django-ewiz',
    packages=['django_ewiz'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.4",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Utilities",
    ],
    install_requires=[
        "Django>=1.5",
        "djangotoolbox>=1.6.2",
        "requests>=2.3.0",
    ],
)
