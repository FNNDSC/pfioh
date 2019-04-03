"""
Handle Swift File Storage Option
"""

import base64
import datetime
import zipfile
import os
import configparser
from   keystoneauth1.identity      import v3
from   keystoneauth1               import session
from   swiftclient                 import service as swift_service
from   pfmisc._colors              import Colors
from   shutil                      import copyfileobj
import pprint

pp = pprint.PrettyPrinter(indent=4)

def _createSwiftService(configPath):
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

    service = swift_service.SwiftService(options)
    return service

def storeData(**kwargs):
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

    swiftService = _createSwiftService(configPath)

    if not b_zip:
        with zipfile.ZipFile('/local/outgoingData.zip', 'w', compression=zipfile.ZIP_DEFLATED) as zipfileObj:
            with zipfileObj.open(str_clientPath.split('/')[-1], 'wb') as entry:
                copyfileobj(inputStream, entry)
    else:
        if not os.path.exists('/local'):
            os.mkdir('/local')
        f = open('/local/outgoingData.zip', "wb")
        buf = 16*1024
        while 1:
            chunk = inputStream.read(buf)
            if not chunk:
                break
            f.write(chunk)
        f.close()
    try:
        success = True
        uploadObject = swift_service.SwiftUploadObject('/local/outgoingData.zip', object_name="input/data")
        uploadResultsGenerator = swiftService.upload(str_containerName, [uploadObject])
        for res in uploadResultsGenerator:
            print("Upload results generated")
            if not res["success"]:
                success = False
            pp.pprint(res)
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


def getData(**kwargs):
    """
    Gets the data from the Swift Storage, zips and/or encodes it and sends it to the client
    """

    b_delete = False
    configPath = "/etc/swift/swift-credentials.cfg"

    for k,v in kwargs.items():
        if k== 'Path': containerName = v
        if k== 'is_zip': b_zip = v
        if k== 'cleanup': b_cleanup = v
        if k== 'd_ret': d_ret = v
        if k == 'configPath': configPath = v
        if k == 'delete': b_delete = v

    swiftService = _createSwiftService(configPath)
	
    key = "output/data"
    success = True
	
    if not os.path.exists('/local'):
        os.mkdir('/local')
    downloadResultsGenerator = swiftService.download(containerName, [key], {'out_file': '/local/incomingData.zip'})
    for res in downloadResultsGenerator:
        print("Download results generated",flush=True)
        if not res['success']:
            success = False
        pp.pprint(res)
    if success:
        print("Download successful")
        if b_delete:
            for res in swiftService.delete(containerName, [key]):
                print("Delete results generated")
                if not res['success']:
                    success = False
                pp.pprint(res)
            if success:
                print('Deleted object with key %s' %key)
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
