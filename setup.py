from distutils.core import setup

setup(
    name='django-ewiz',
    version='1.1.2',
    packages=['django_ewiz'],
    license=open('LICENSE.txt').read(),
    description="A non-relational Django database backend that utilizes EnterpriseWizard's REST interface.",
    long_description=open('README.txt').read(),
    install_requires=[
        "Django>=1.5.2",
        "djangotoolbox==0.9.2"
    ],
)
