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
import json
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
            if k == 'input_stream': inputStream     = v
            if k == 'client_path': str_clientPath   = v
            if k == 'path': str_destPath            = v
            if k == 'is_zip': b_zip                 = v
            if k == 'd_ret': d_ret                  = v

        if not os.path.exists(str_destPath):
            os.mkdir(str_destPath)
        if b_zip:
            with zipfile.ZipFile(inputStream, 'r') as zipfileObj:
                zipfileObj.extractall(path=str_destPath)
            d_ret['write']['file'] = str_destPath
        else:
            filePath = os.path.join(str_destPath, str_clientPath.split('/')[-1])
            f = open(filePath, 'wb')
            buf = 16*1024
            while 1:
                chunk = inputStream.read(buf)
                if not chunk:
                    break
                f.write(chunk)
            f.close()
            d_ret['write']['file'] = filePath
        d_ret['write']['status']    = True
        d_ret['write']['msg']       = 'File written successfully!'
        d_ret['write']['timestamp'] = '%s' % datetime.datetime.now()
        d_ret['status']             = True
        d_ret['msg']                = d_ret['write']['msg']

        return d_ret


    def getData(self, **kwargs):
        """
        Gets the file/directory from the specified location,
        zips and/or encodes it and sends it to the client

        Note an implicit assumption can sometimes result
        in error conditions in case where no files were
        generated by the compute -- this necessitated some
        checks on the `str_fileToProcess` variable.

        In the case where no files were generated, a dummy
        JSON text file is created and returned with
        appropriate internal content.
        """

        def emptyDirWarningFile_create(str_path):
            """
            In the case where the compute has not generated
            any files, create a warning file to return to the
            client.
            """
            d_warning       : dict  = {
                'message'   : 'Warning! No files were created by the compute!'
            }
            try:
                os.mkdir(str_path)
            except:
                pass
            with open('%s/computeCreatedNoFiles.json' % str_path, 'w') as fp:
                json.dump(d_warning, fp)
            fp.close()


        def filePath_zipContents(str_path, zipObj):
            """
            Zip to contents of str_path to passed zipObj
            and return a count of zipped files.
            """
            fileCount   :   int = 0
            for root, dirs, files in os.walk(str_path):
                for filename in files:
                    fileCount   += 1
                    arcname     = os.path.join(
                        root, filename
                        )[len(str_localPath.rstrip(os.sep))+1:]
                    zipObj.write(
                        os.path.join(root, filename),
                        arcname = arcname
                    )
            return fileCount

        str_fileToProcess   : str   = ''
        str_warnPath        : str   = '/tmp/warn'

        for k,v in kwargs.items():
            if k == 'path':     str_localPath   = v
            if k == 'is_zip':   b_zip           = v
            if k == 'cleanup':  b_cleanup       = v
            if k == 'd_ret':    d_ret           = v
            if k == 'key':      key             = v

        if b_zip:
            str_fileToProcess = "/tmp/{}.zip".format(key)
            with zipfile.ZipFile(
                                    str_fileToProcess,
                                    'w',
                                    compression = zipfile.ZIP_DEFLATED
                                ) as zipfileObj:
                if not filePath_zipContents(str_localPath, zipfileObj):
                    emptyDirWarningFile_create(str_localPath)
                    filePath_zipContents(str_localPath, zipfileObj)
        else:
            str_fileToProcess = os.walk(str_localPath).next()[2][0]
        d_ret['status'] = True
        d_ret['msg'] = "File/Directory downloaded"
        if len(str_fileToProcess):
            self.buffered_response(str_fileToProcess)
        if b_cleanup:
            if b_zip:
                self.dp.qprint(
                    "Removing '%s'..." % (str_fileToProcess),
                    comms = 'status'
                )
                if os.path.isfile(str_fileToProcess):
                    os.remove(str_fileToProcess)
        return d_ret
