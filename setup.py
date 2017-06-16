import  sys
from    setuptools import setup

# Make sure we are running python3.5+
if 10 * sys.version_info[0]  + sys.version_info[1] < 35:
    sys.exit("Sorry, only Python 3.5+ is supported.")


def readme():
    with open('README.rst') as f:
        return f.read()

setup(
      name             =   'pfioh',
      version          =   '1.2.6',
      description      =   'Path-and-File-IO-over-HTTP',
      long_description =   readme(),
      author           =   'Rudolph Pienaar',
      author_email     =   'rudolph.pienaar@gmail.com',
      url              =   'https://github.com/FNNDSC/pman',
      packages         =   ['pfioh'],
      install_requires =   ['pycurl', 'pyzmq', 'webob', 'pudb', 'psutil'],
      test_suite       =   'nose.collector',
      tests_require    =   ['nose'],
      scripts          =   ['bin/pfioh'],
      license          =   'MIT',
      zip_safe         =   False
     )
