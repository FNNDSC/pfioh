##Swift Object Store

The OpenStack Object Store project, known as Swift, offers cloud storage software so that you can store and retrieve lots of data with a simple API. It's built for scale and optimized for durability, availability, and concurrency across the entire data set. Swift is ideal for storing unstructured data that can grow without bound. 

To enable Swift Object store option for pfioh, start pfioh with --swift-storage option
`pfioh --forever --httpResponse --swift-storage --createDirsAsNeeded`

The pushPath and pullPath operations are same as mentioned for mounting directories method.

The credentials file for Swift should be stored in a **secret**, mounted at `/etc/swift` in the pod with the name `‘swift-credentials.cfg’`. It should contain the swift credentials in the following format:

>[AUTHORIZATION]
>osAuthUrl  =	
>username   = 
>password   = 
>
>[PROJECT]
>osProjectDomain  = 
>osProjectName    = 

#Creating a secret
1) Create a text file with the name swift-credentials.cfg as shown above.

2) Now run the following command to create a secret
`oc create secret generic swift-credentials --from-file=<path-to-file>/swift-credentials.cfg`

3) Now attach this secret to the pod, by clicking *add config files to <dc-name>* 

4) Select the secret and use the mount path `/etc/swift`

