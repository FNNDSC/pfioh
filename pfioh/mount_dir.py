"""
Handle MountDir file storage
"""

import shutil
import datetime
import zipfile
import zlib
import gzip
import base64
import os
import ast
from   io                   import BytesIO
from   io                   import StringIO
from   pfioh                import StoreHandler
from   pfioh                import base64_process, zip_process, zipdir
from   pfmisc._colors       import Colors

import pudb

class MountDir(StoreHandler):

    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dp.qprint('MountDir initialized')
        

    def storeData(self, **kwargs):
        """
        Stores the file/directory at the specified location
        """

        for k,v in kwargs.items():
            if k == 'file_name': fileName  = v
            if k == 'file_content': fileContent = v
            if k == 'Path': unpackPath= v
            if k == 'is_zip': b_zip= v
            if k == 'd_ret': d_ret= v

        try:
            with open(fileName, 'wb') as fh:
                try:
                    fh.write(fileContent)
                except Exception as err:
                    self.dp.qprint(err)

        finally:
            if b_zip:
                d_fio = zip_process(
                    action= 'unzip',
                    path= unpackPath,
                    payloadFile = fileName
                )
                d_ret['unzip']  = d_fio
                d_ret['status'] = d_fio['status']
                d_ret['msg']    = d_fio['msg']
                d_ret['write']['filesize']  = "{:,}".format(self.getSize(fileName))
                os.remove(fileName)

        # pudb.set_trace()
        d_ret['write']['file']      = fileName
        d_ret['write']['status']    = True
        d_ret['write']['msg']       = 'File written successfully!'
        # d_ret['write']['filesize']  = "{:,}".format(fileSize)
        # d_ret['write']['filesize']  = "{:,}".format(os.stat(fileName).st_size)
        d_ret['write']['timestamp'] = '%s' % datetime.datetime.now()
        d_ret['status']             = True
        d_ret['msg']                = d_ret['write']['msg']

        return d_ret


    def getData(self, **kwargs):
        """
        Gets the file/directory from the specified location, zips and/or encodes it
        and sends it to the client
        """

        for k,v in kwargs.items():
            if k== 'path': str_fileToProcess= v 
            if k== 'is_zip': b_zip= v
            if k== 'cleanup': b_cleanup= v
            if k== 'd_ret': d_ret= v
    
        #Zipping
        if b_zip:
            self.dp.qprint("Zipping target '%s'..." % str_fileToProcess, comms = 'status')
 
            str_dirSuffix   = ""
            # Ensure that directory paths end in '/'
            if os.path.isdir(str_fileToProcess) and str_fileToProcess[-1] != '/':
                str_dirSuffix   = '/'
            d_fio   = zip_process(
                action  = 'zip',
                path    = str_fileToProcess,
                arcroot = str_fileToProcess + str_dirSuffix
            )
            d_ret['zip']        = d_fio
            d_ret['status']     = d_fio['status']
            d_ret['msg']        = d_fio['msg']
            d_ret['timestamp']  = '%s' % datetime.datetime.now()
           
            if not d_ret['status']:
                self.dp.qprint("An error occurred during the zip operation:\n%s" % d_ret['msg'],
                             comms = 'error')
                self.ret_client(d_ret)
                return d_ret

            str_fileToProcess        = d_fio['fileProcessed']
            str_zipFile              = str_fileToProcess
            d_ret['zip']['filesize'] = self.getSize(str_fileToProcess)
            self.dp.qprint("Zip file: " + Colors.YELLOW + "%s" % str_zipFile +
                Colors.PURPLE + '...' , comms = 'status')

        try:
            #Reading from file
            d_ret = self.readData(str_fileToProcess, d_ret)

        finally:
            #Cleanup by deleting temporary files
            if b_cleanup:
                if b_zip:
                    self.dp.qprint("Removing '%s'..." % (str_zipFile), comms = 'status')
                    if os.path.isfile(str_zipFile):     os.remove(str_zipFile)

        return d_ret


    def readData(self, str_fileToProcess, d_ret):
        """
        Reads the data from the file and writes it for transferring over the network
        """

        with open(str_fileToProcess, 'rb') as fh:
            filesize    = os.stat(str_fileToProcess).st_size
            self.dp.qprint("Transmitting " + Colors.YELLOW + "{:,}".format(filesize) + Colors.PURPLE +
                        " target bytes from " + Colors.YELLOW + 
                        "%s" % (str_fileToProcess) + Colors.PURPLE + '...', comms = 'status')
            self.send_response(200)
            # self.send_header('Content-type', 'text/json')
            self.end_headers()
            # try:
            #     self.wfile.write(fh.read().encode())
            # except:
            self.dp.qprint('<transmission>', comms = 'tx')
            d_ret['transmit']               = {}
            d_ret['transmit']['msg']        = 'transmitting'
            d_ret['transmit']['timestamp']  = '%s' % datetime.datetime.now()
            d_ret['transmit']['filesize']   = '%s' % os.stat(str_fileToProcess).st_size
            d_ret['status']                 = True
            d_ret['msg']                    = d_ret['transmit']['msg']
            self.wfile.write(fh.read())

        return d_ret

    def getSize(self, str_fileToProcess):
        """
        Returns the size of the given file
        """
        
        return os.stat(str_fileToProcess).st_size
