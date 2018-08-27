####################
pfioh - v1.5.16.0
####################

.. image:: https://badge.fury.io/py/pman.svg
    :target: https://badge.fury.io/py/pfioh

.. image:: https://travis-ci.org/FNNDSC/pfioh.svg?branch=master
    :target: https://travis-ci.org/FNNDSC/pfioh

.. image:: https://img.shields.io/badge/python-3.5%2B-blue.svg
    :target: https://badge.fury.io/py/pfioh

.. contents:: Table of Contents

********
Overview
********

This repository provides ``pfioh`` -- a *server* process (think of it as anonymous ``ftp`` that natively understands recursive paths) that allows for file/path push/copy.

- ``pfioh``: a *file* IO manager;

pfioh
=====

``pfioh`` is a service that pushes/pulls files and directories between different locations.


************
Installation
************

Installation is relatively straightforward, and we recommend using either python virtual environments or docker.

Python Virtual Environment
==========================

On Ubuntu, install the Python virtual environment creator

.. code-block:: bash

  sudo apt install virtualenv

Then, create a directory for your virtual environments e.g.:

.. code-block:: bash

  mkdir ~/python-envs

You might want to add to your .bashrc file these two lines:

.. code-block:: bash

    export WORKON_HOME=~/python-envs
    source /usr/local/bin/virtualenvwrapper.sh

Then you can source your .bashrc and create a new Python3 virtual environment:

.. code-block:: bash

    source .bashrc
    mkvirtualenv --python=python3 python_env

To activate or "enter" the virtual env:

.. code-block:: bash

    workon python_env

To deactivate virtual env:

.. code-block:: bash

    deactivate

Using the ``fnndsc/pfioh`` dock
===============================

The easiest option however, is to just use the ``fnndsc/pfioh`` dock.

.. code-block:: bash

    docker pull fnndsc/pfioh
    
and then run

.. code-block:: bash

    docker run --name pfioh -v /home:/Users --rm  fnndsc/pfioh --forever --httpResponse --storeBase=/tmp --createDirsAsNeeded

*****
Usage
*****

``pfioh`` usage
===============

For ``pfioh`` detailed information, see the `pfioh wiki page <https://github.com/FNNDSC/pfioh/wiki/pfioh-overview>`_.

.. code-block:: html

        [--ip <IP>]                            

        The IP interface on which to listen. Default %s.

        [--port <port>]
        The port on which to listen. Defaults to '5055'.

        [--man <manpage>]
        Internal man page with more detail on specific calls.

        [--forever]
        Start service and do not terminate.

        [--httpResponse]
        Send return strings as HTTP formatted replies with content-type html.

        [--storeBase <storagePath>]
        A file system location in the network space accessible to ``pfioh``
        that is used to unpack received files and also store results of
        processing.

        [--createDirsAsNeeded]
        If specified, create dirs in the base storage as needed.

        [--test]
        Run internal tests.

        [-x|--desc]                                     
        Provide an overview help page.

        [-y|--synopsis]
        Provide a synopsis help summary.

        [--version]
        Print internal version number and exit.

        [-v|--verbosity <level>]
        Set the verbosity level. "0" typically means no/minimal output. Allows for
        more fine tuned output control as opposed to '--quiet' that effectively
        silences everything.

********
EXAMPLES
********

Start ``pfioh`` in forever mode:

.. code-block:: bash

            pfioh                                                   \\
                --forever                                           \\
                --ip %s                                      \\
                --port 5055                                         \\
                --storeBase=/tmp                                    \\
                --httpResponse                                      \\
                --createDirsAsNeeded                                \\
                --verbosity 1



