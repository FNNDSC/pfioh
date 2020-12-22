from os import path
from setuptools import setup

with open(path.join(path.abspath(path.dirname(__file__)), 'README.rst')) as f:
    readme = f.read()

setup(
    name             =   'pfioh',
    version          =   '3.0.0.2',
    description      =   'Path-and-File-IO-over-HTTP',
    long_description =   readme,
    author           =   'Rudolph Pienaar',
    author_email     =   'rudolph.pienaar@gmail.com',
    url              =   'https://github.com/FNNDSC/pfioh',
    packages         =   ['pfioh'],
    install_requires =   ['pycurl', 'pyzmq', 'webob', 'pudb', 'psutil', 'keystoneauth1', 'python-keystoneclient', 'python-swiftclient', 'pfmisc==2.0.2'],
    test_suite       =   'nose.collector',
    tests_require    =   ['nose'],
    scripts          =   ['bin/pfioh'],
    license          =   'MIT',
    zip_safe         =   False,
    python_requires  =   '>=3.6'
)
