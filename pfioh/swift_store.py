"""
Handle Swift File Storage Option
"""

import ast
import base64
import datetime
import zlib
import zipfile
import os
import configparser
from pfioh import StoreHandler
from pfioh import base64_process, zip_process, zipdir
from keystoneauth1.identity import v3
from keystoneauth1 import session
from swiftclient import client as swift_client
try:
    from ._colors import Colors
except:
    from _colors import Colors

class SwiftStore(StoreHandler):

    swiftConnection = ''
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.qprint('SwiftStore initialized')
        

    def _getScopedSession(self, osAuthUrl, username, password, osProjectDomain, osProjectName):
        """
        Uses keystone authentication to create and return a scoped session
        """

        passwordAuth  = v3.Password(auth_url= osAuthUrl,
                            user_domain_name= 'default',
                            username= username, password= password,
                            project_domain_name= osProjectDomain,
                            project_name= osProjectName,
                            unscoped= False)

        scopedSession = session.Session(auth= passwordAuth)
        return scopedSession


    def _initiateSwiftConnection(self, **kwargs):
        """
        Initiates a Swift connection and returns a Swift Connection Object
        Swift credentials should be stored as a cfg file at /etc/swift 
        """

        for k,v in kwargs:
            if k == 'configPath': configPath= v

        configPath= '/etc/swift/swift-credentials.cfg'

        config= configparser.ConfigParser()
        f = open(configPath, 'r')
        config.readfp(f)
        f.close()
        
        osAuthUrl = config['AUTHORIZATION']['osAuthUrl']
        username= config['AUTHORIZATION']['username']
        password= config['AUTHORIZATION']['password']
        osProjectDomain= config['PROJECT']['osProjectDomain']
        osProjectName= config['PROJECT']['osProjectName']
        
        scopedSession = self._getScopedSession(osAuthUrl, username, password, osProjectDomain, osProjectName)
        self.swiftConnection = swift_client.Connection(session=scopedSession)
            

    def _deleteEmptyDirectory(self, key):
        """
        Deletes the empty directory created by Swift in the parent directory
        """

        directoryPath = os.path.join(os.path.dirname(__file__), '../%s'%key)
        try:
            os.rmdir(directoryPath)
            self.qprint("Temporary directory %s deleted"%key)
        except:
            self.qprint("No temporary directory found")


    def _putContainer(self, key):
        """
        Creates a container with the name as the key
        """

        try:
            self.swiftConnection.put_container(key)
            self.qprint('Container added sucessfully')
        except Exception as exp:
            self.qprint(exp)


    def _putObject(self, containerName, key, value):
        """
        Creates an object with the given key and value and puts the object in the specified container
        """

        try:
            self.swiftConnection.put_object(containerName, key , contents=value, content_type='text/plain')
            self.qprint('Object added with key %s' %key)

        except Exception as exp:
            self.qprint('Exception = %s' %exp)


    def _getObject(self, key, b_delete):
        """
        Returns an object associated with the specified key in the specified container
        Deletes the object after returning if specified
        """

        try:
            containerName = key
            key = os.path.join('input','data')
            swiftDataObject = self.swiftConnection.get_object(containerName, key)
            if b_delete:
                self.swiftConnection.delete_object(containerName, key)
                self.qprint('Deleted object with key %s' %key)

        except Exception as exp:
            self.qprint(exp)

        return swiftDataObject


    def doZipping(self, fileContent, clientFile):
        """
        Zips up the file content byte stream, reads from archive and returs zipped content
        """

        fileName = clientFile.split('/')[-1]

        zipfileObj = zipfile.ZipFile('ziparchive.zip', 'w' ,compression= zipfile.ZIP_DEFLATED)
        zipfileObj.writestr(fileName,fileContent)

        with open('ziparchive.zip','rb') as f:
            zippedFileContent = f.read()

        os.remove('ziparchive.zip')

        return zippedFileContent


    def storeData(self, **kwargs):
        """
        Creates an object of the file and stores it into the container as key-value object 
        """

        for k,v in kwargs.items():
            if k == 'file_content':   fileContent = v
            if k == 'Path': 	      key         = v
            if k == 'is_zip':         b_zip       = v
            if k == 'd_ret':          d_ret       = v
            if k == 'client_path':    clientFile  = v

        try:
            self._initiateSwiftConnection()
            self._putContainer(key)
        except:
            d_ret['msg']    =  'Key already exists, use a different key'
            d_ret['status'] =  False
            return d_ret

        if not b_zip:
            fileContent = self.doZipping(fileContent, clientFile)

        try:
            containerName = key
            key           = os.path.join('input','data')
            self._putObject(containerName, key, fileContent)
        except Exception as err:
            self.qprint(err)
            d_ret['msg']    = 'File/Directory not stored in Swift'
            d_ret['status'] = False
            return d_ret

        #Delete temporary empty directory created by Swift
        self._deleteEmptyDirectory(key)

        #Headers 
        d_ret['status'] = True
        d_ret['msg']    = 'File/Directory stored in Swift'

        return d_ret


    def getData(self, **kwargs):
        """
        Gets the data from the Swift Storage, zips and/or encodes it and sends it to the client
        """

        for k,v in kwargs.items():
            if k== 'path': key= v
            if k== 'is_zip': b_zip= v
            if k== 'encoding': str_encoding= v
            if k== 'cleanup': b_cleanup= v
            if k== 'd_ret': d_ret= v


        try:
            self._initiateSwiftConnection()
            dataObject = self._getObject(key, False)
        except Exception as err:
            self.qprint(err)
            d_ret['status'] = False
            d_ret['msg']    = 'Retriving File/Directory from Swift failed'
            return d_ret

        objectInformation= dataObject[0]
        objectValue= dataObject[1]
        fileContent= objectValue
    
        #Unzipping
        if not b_zip:
            raise NotImplementedError('Please use the zip option')

        #Encoding
        if str_encoding=='base64':
            try:
                fileContent         = base64.b64encode(fileContent)
                self.qprint('Base64 encoding successful')

                d_fio               = {
                    'msg':            'Encode successful',
                    'status':         True
                }
                d_ret['encode']     = d_fio
                d_ret['status']     = d_fio['status']
                d_ret['msg']        = d_fio['msg']
                d_ret['timestamp']  = '%s' % datetime.datetime.now()

            except Exception as err:
                self.qprint(err)
                d_fio               = {
                    'msg':            'Encode unsuccessful',
                    'status':         False
                }
                d_ret['encode']     = d_fio
                d_ret['status']     = d_fio['status']
                d_ret['msg']        = d_fio['msg']
                d_ret['timestamp']  = '%s' % datetime.datetime.now()
                return d_ret              
        
        self.writeData(fileContent)        

        #Transmit the file
        d_ret['status'] = True

        #Delete temporary empty directory created by Swift
        self._deleteEmptyDirectory(key)

        return d_ret


    def writeData(self, fileContent):
        """
        Writes the file content into a wfile object for transferring over the network
        """

        return self.wfile.write(fileContent)
         
