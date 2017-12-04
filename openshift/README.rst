##############
Setup:
##############

We intend to use Swift Object store as default backend for pfioh in the OpenShift template.

##############
Swift Object Store
##############

The OpenStack Object Store project, known as Swift, offers cloud storage software so that you can store and retrieve lots of data with a simple API. It's built for scale and optimized for durability, availability, and concurrency across the entire data set. Swift is ideal for storing unstructured data that can grow without bound. 

To enable Swift Object store option for pfioh, start pfioh with --swift-storage option (this has been already taken care of if you are using the OpenShift template available in this repo).

.. code-block:: bash

    pfioh --forever --httpResponse --swift-storage --createDirsAsNeeded

The pushPath and pullPath operations are same as mentioned for mounting directories method.

The credentials file for Swift should be stored in a **secret**, mounted at /etc/swift in the pod with the name ‘swift-credentials.cfg’. It should contain the swift credentials in the following format:


.. code-block:: bash
    
    [AUTHORIZATION]
    osAuthUrl  =   
    username   = 
    password   = 

    [PROJECT]
    osProjectDomain  = 
    osProjectName    = 

**************
Creating a secret and running pfioh
**************
1) Create a text file with the name swift-credentials.cfg as shown above.


2) Now run the following command to create a secret

.. code-block:: bash

    oc create secret generic swift-credentials --from-file=<path-to-file>/swift-credentials.cfg

Note: This is only required for pfioh which uses OpenStack Swift Object store.

3) Run pfioh.

.. code-block:: bash

    oc new-app openshift/pfioh-openshift-template.json 

   

