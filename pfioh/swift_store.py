"""
Handle Swift File Storage Option
"""

import base64
import datetime
import zipfile
import os
import configparser
from   pfioh                       import HandleRequests
from   keystoneauth1.identity      import v3
from   keystoneauth1               import session
from   swiftclient                 import service as swift_service
from   pfmisc._colors              import Colors
from   shutil                      import copyfileobj
import pprint

pp = pprint.PrettyPrinter(indent=4)


class SwiftStore():

    def __init__(self):
        HandleRequests.dp.qprint('SwiftStore initialized')

    def _createSwiftService(self, configPath):
        config = configparser.ConfigParser()
        f = open(configPath, 'r')
        config.readfp(f)
        f.close()

        options = {
            'auth_version':         3,
            'os_auth_url':          config['AUTHORIZATION']['osAuthUrl'],
            'os_username':          config['AUTHORIZATION']['username'],
            'os_password':          config['AUTHORIZATION']['password'],
            'os_project_domain_name':    config['PROJECT']['osProjectDomain'],
            'os_project_name':      config['PROJECT']['osProjectName']
        }

        auth_swift = v3.oidc.OidcPassword(
            options['os_auth_url'],
            identity_provider='moc',
            protocol='openid',
            client_id='kaizen-client',
            client_secret='fac377a9-f2ba-41e7-bb7f-4064dd9f4468',
            access_token_endpoint='https://sso.massopen.cloud/auth/realms/moc/protocol/openid-connect/token',
            discovery_endpoint='https://sso.massopen.cloud/auth/realms/moc/.well-known/openid-configuration',
            username=options['os_username'],
            password=options['os_password'],
            project_name=options['os_project_name'],
            project_domain_name=options['os_project_domain_name']
        )

        session_client = session.Session(auth=auth_swift)
        service = swift_service.Connection(session=session_client)
        return service

    def storeData(self, **kwargs):
        """
        Creates an object of the file and stores it into the container as key-value object 
        """

        configPath = "/etc/swift/swift-credentials.cfg"
        
        for k,v in kwargs.items():
            if k == 'input_stream': inputStream         = v
            if k == 'path':         str_containerName   = v
            if k == 'is_zip':       b_zip               = v
            if k == 'd_ret':        d_ret               = v
            if k == 'client_path':  str_clientPath      = v
            if k == 'configPath':   configPath          = v
            if k == 'key':          key                 = v

        swiftService = self._createSwiftService(configPath)

        if not b_zip:
            with zipfile.ZipFile('/tmp/{}.zip'.format(key), 'w', compression=zipfile.ZIP_DEFLATED) as zipfileObj:
                with zipfileObj.open(str_clientPath.split('/')[-1], 'wb') as entry:
                    copyfileobj(inputStream, entry)
        else:
            f = open('/tmp/{}.zip'.format(key), 'wb')
            buf = 16*1024
            while 1:
                chunk = inputStream.read(buf)
                if not chunk:
                    break
                f.write(chunk)
            f.close()

        zip_file_contents = open('/tmp/{}.zip'.format(key), mode='rb')

        try:
            success = True
            filePath = "input/data"

            resp_headers, containers = swiftService.get_account()
            listContainers = [d['name'] for d in containers if 'name' in d]

            if str_containerName not in listContainers:
                swiftService.put_container(str_containerName)
                resp_headers, containers = swiftService.get_account()
                listContainers = [d['name'] for d in containers if 'name' in d]
                if str_containerName in listContainers:
                    print("The container was created successfully")
                else:
                    raise Exception("The container was not created successfully")

            swiftService.put_object(
                str_containerName,
                filePath,
                contents=zip_file_contents,
                content_type='application/zip'
            )
            zip_file_contents.close()

            # Confirm presence of the object in swift
            response_headers = swiftService.head_object(str_containerName, filePath)
            print('The upload was successful')
        except Exception as err:
            print(err)
            success = False

        #Headers 
        if success:
            d_ret['status'] = True
            d_ret['msg'] = 'File/Directory stored in Swift'
        else:
            d_ret['status'] = False
            d_ret['msg'] = 'File/Directory not stored in Swift'

        return d_ret


    def getData(self, **kwargs):
        """
        Gets the data from the Swift Storage, zips and/or encodes it and sends it to the client
        """

        b_delete = False
        configPath = "/etc/swift/swift-credentials.cfg"

        for k,v in kwargs.items():
            if k== 'path': containerName = v
            if k== 'is_zip': b_zip = v
            if k== 'cleanup': b_cleanup = v
            if k== 'd_ret': d_ret = v
            if k == 'configPath': configPath = v
            if k == 'delete': b_delete = v

        swiftService = self._createSwiftService(configPath)
            
        key = "output/data"
        success = True
            
        response_headers, object_contents = swiftService.get_object(containerName, key)

        # Download the object
        try:
            downloaded_file = open('/tmp/incomingData.zip', mode='wb')
            downloaded_file.write(object_contents)
            downloaded_file.close()
            print("Download results generated", flush=True)
        except Exception as e:
            success = False
            pp.pprint(e)

        if success:
            print("Download successful")
            if b_delete:
                try:
                    swiftService.delete_object(containerName, key)
                except Exception as e:
                    success = False
                    pp.pprint(e)
                if success:
                    print('Deleted object with key %s' % key)
                else:
                    print("Deletion unsuccessful")
        else:
            print("Download unsuccessful")

        if success:
            d_ret['status'] = True
            d_ret['msg'] = 'File/Directory downloaded'
        else:
            d_ret['status'] = False
            d_ret['msg'] = 'File/Directory downloaded'

        #Unzipping
        if not b_zip:
            raise NotImplementedError('Please use the zip option')

        return d_ret
