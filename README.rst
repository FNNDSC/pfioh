#####
pfioh
#####

.. image:: https://img.shields.io/docker/v/fnndsc/pfioh
    :target: https://hub.docker.com/r/fnndsc/pfioh

.. image:: https://img.shields.io/github/license/fnndsc/pfioh
    :target: https://github.com/FNNDSC/pfioh/blob/master/LICENSE

.. contents:: Table of Contents

********
Overview
********

This repository provides ``pfioh`` -- a *server* process (think of it as anonymous ``ftp`` that natively understands recursive paths) that allows for file/path push/copy.

*****
Usage
*****

For ``pfioh`` detailed information, see the `pfioh wiki page <https://github.com/FNNDSC/pfioh/wiki/pfioh-overview>`_.

.. code-block:: html

        [--ip <IP>]                            

        The IP interface on which to listen. Defaults to current host IP.

        [--port <port>]
        The port on which to listen. Defaults to '5055'.

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

        [--enableTokenAuth]
        Enables token based authorization and can be configured to look for a .ini 
        file or an openshift secret.
        
        [--tokenPath <tokenPath>]
        Specify the absolute path to the token in the file system.
        By default, this looks for the pfiohConfig.ini file in the current working directory.

        [--swift-storage]
        If specified, use Swift as object storage.

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

*******
Example
*******

.. code-block:: bash

    docker run --rm --name pfioh  \
        -v $PWD/base:/base        \
        -p 5055:5055              \
        fnndsc/pfioh:latest       \
        --forever --httpResponse  \
        --storeBase=/base         \
        --createDirsAsNeeded      \
        --port 5055
