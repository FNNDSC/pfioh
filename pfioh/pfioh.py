#!/usr/bin/env python3

import  sys
import  stat

from    io              import  BytesIO as IO
from    http.server     import  BaseHTTPRequestHandler, HTTPServer
from    socketserver    import  ThreadingMixIn
from    webob           import  Response
import  cgi
import  json
import  base64
import  zipfile
import  uuid
import  urllib
import  ast
import  shutil
import  datetime
import  tempfile
import  pprint

import  platform
import  socket
import  psutil
import  os
import  multiprocessing
import  inspect
import  pudb
import  inspect
import  pfmisc
from pfmisc.Auth import Auth

# pfioh local dependencies
from    pfmisc._colors  import Colors
from    pfmisc.debug    import debug

# Global var
Gd_internalvar = {
    'name':                 "pfioh",
    'version':              "",
    'verbosity':            0,
    'storeBase':            "/tmp",
    'key2address':          {},
    'httpResponse':         False,
    'createDirsAsNeeded':   False,
    'b_swiftStorage':       False,
    'b_tokenAuth':          False,
    'authModule':           None
}

class StoreHandler(BaseHTTPRequestHandler):

    b_quiet     = False

    def __init__(self, *args, **kwargs):
        """
        """
        global  Gd_internalvar
        self.__auth             = None
        self.__name__           = 'StoreHandler'
        self.d_ctlVar           = Gd_internalvar
        b_test                  = False
        self.__b_tokenAuth      = Gd_internalvar['b_tokenAuth']

        self.b_useDebug         = False
        self.str_debugFile      = '/tmp/pfioh-log.txt'
        self.b_quiet            = True
        self.dp                 = pfmisc.debug(    
                                            verbosity   = Gd_internalvar['verbosity'],
                                            within      = self.__name__
                                            )
        self.pp                 = pprint.PrettyPrinter(indent=4)

        if self.__b_tokenAuth:
            self.__auth    = Gd_internalvar['authModule']

        for k,v in kwargs.items():
            if k == 'test'  : b_test   = True
            if k == 'tokenAuth': self.__b_tokenAuth = v

        if not b_test:
            BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

    def qprint(self, msg, **kwargs):
        str_comms  = ""
        for k,v in kwargs.items():
            if k == 'comms':    str_comms  = v

        str_caller  = inspect.stack()[1][3]

        if not StoreHandler.b_quiet:
            if str_comms == 'status':   print(Colors.PURPLE,    end="")
            if str_comms == 'error':    print(Colors.RED,       end="")
            if str_comms == "tx":       print(Colors.YELLOW + "<----")
            if str_comms == "rx":       print(Colors.GREEN  + "---->")
            print('%s' % datetime.datetime.now() + " | "  + os.path.basename(__file__) + ':' + self.__name__ + "." + str_caller + '() | ', end="")
            print(msg)
            if str_comms == "tx":       print(Colors.YELLOW + "<----")
            if str_comms == "rx":       print(Colors.GREEN  + "---->")
            print(Colors.NO_COLOUR, end="", flush=True)

    def remoteLocation_resolve(self, d_remote):
        """
        Resolve the remote path location

        :param d_remote: the "remote" specification
        :return: a string representation of the remote path
        """
        b_status        = False
        str_remotePath  = ""

        if Gd_internalvar['b_swiftStorage']:
            b_status= True
            str_remotePath= d_remote['key']
        elif 'path' in d_remote.keys():
            str_remotePath  = d_remote['path']
            b_status        = True
        elif 'key' in d_remote.keys():
            d_ret =  self.storage_resolveBasedOnKey(key = d_remote['key'])
            if d_ret['status']:
                b_status        = True
                str_remotePath  = d_ret['path']
        return {
            'status':   b_status,
            'path':     str_remotePath
        }

    def do_GET_remoteStatus(self, d_msg, **kwargs):
        """
        This method is used to get information about the remote
        server -- for example, is a remote directory/file valid?
        """

        global Gd_internalvar

        d_meta              = d_msg['meta']
        d_remote            = d_meta['remote']

        str_serverPath      = self.remoteLocation_resolve(d_remote)['path']
        self.dp.qprint('server path resolves to %s' % str_serverPath, comms = 'status')

        b_isFile            = os.path.isfile(str_serverPath)
        b_isDir             = os.path.isdir(str_serverPath)
        b_exists            = os.path.exists(str_serverPath)
        
        self.dp.qprint('b_isfile:  %r' % b_isFile, comms = 'status')
        self.dp.qprint('b_isDir:   %r' % b_isDir,  comms = 'status')
        self.dp.qprint('b_exists:  %r' % b_exists, comms = 'status')

        b_createdNewDir     = False
        b_swiftStore        = False
        
        if Gd_internalvar['b_swiftStorage']:
            b_exists     = True
            b_swiftStore = True 

        if not b_exists and Gd_internalvar['createDirsAsNeeded']:
            os.makedirs(str_serverPath)
            b_createdNewDir = True

        d_ret               = {
            'status':           b_exists or b_createdNewDir,
            'isfile':           b_isFile,
            'isswiftstore':     b_swiftStore,
            'isdir':            b_isDir,
            'createdNewDir':    b_createdNewDir
        }

        self.send_response(200)
        self.end_headers()

        self.ret_client(d_ret)
        self.dp.qprint(d_ret, comms = 'tx')

        return {'status': b_exists or b_createdNewDir}

    def do_GET_withCompression(self, d_msg):
        """
        Process a "GET" using zip

        :return:
        """

        # d_msg               = ast.literal_eval(d_server)
        d_meta              = d_msg['meta']
        # d_local             = d_meta['local']
        d_remote            = d_meta['remote']
        d_transport         = d_meta['transport']
        d_compress          = d_transport['compress']
        d_ret               = {}

        str_serverPath      = self.remoteLocation_resolve(d_remote)['path']
        d_ret['preop']      = self.do_GET_preop(    meta          = d_meta,
                                                    path          = str_serverPath)
        if d_ret['preop']['status']:
            str_serverPath      = d_ret['preop']['outgoingPath']
        str_fileToProcess   = str_serverPath

        b_cleanup           = False
        # b_zip               = True
        
        if 'cleanup' in d_compress: b_cleanup = d_compress['cleanup']

        str_archive         = d_compress['archive']
        if str_archive == 'zip':    b_zip = True
        else:                       b_zip = False
        if os.path.isdir(str_serverPath):
            b_zip           = True
            # str_archive    = 'zip'

        d_ret = self.getData(  
                                path        = str_fileToProcess, 
                                is_zip      = b_zip,
                                cleanup     = b_cleanup, 
                                d_ret       = d_ret
                            )
        
        d_ret['postop']      = self.do_GET_postop(  meta          = d_meta)
        self.ret_client(d_ret)
        self.dp.qprint(self.pp.pformat(d_ret).strip(), comms = 'tx')

        return d_ret

    def getData(self, **kwargs):
        raise NotImplementedError('Abstract Method: Please implement this method in child class')

    def do_GET_withCopy(self, d_msg):
        """
        Process a "GET" using copy operations

        :return:
        """

        d_meta              = d_msg['meta']
        d_local             = d_meta['local']
        d_remote            = d_meta['remote']
        d_transport         = d_meta['transport']
        d_copy              = d_transport['copy']

        str_serverPath      = self.remoteLocation_resolve(d_remote)['path']
        str_clientPath      = d_local['path']
        # str_fileToProcess   = str_serverPath

        b_copyTree          = False
        b_copyFile          = False
        b_symlink           = False

        d_ret               = {'status': True}

        if not d_copy['symlink']:
            if os.path.isdir(str_serverPath):
                b_copyTree      = True
                str_serverNode  = str_serverPath.split('/')[-1]
                try:
                    shutil.copytree(str_serverPath, os.path.join(str_clientPath, str_serverNode))
                except BaseException as e:
                    d_ret['status'] = False
                    d_ret['msg']    = str(e)
            if os.path.isfile(str_serverPath):
                b_copyFile      = True
                shutil.copy2(str_serverPath, str_clientPath)
        if d_copy['symlink']:
            str_serverNode  = str_serverPath.split('/')[-1]
            try:
                os.symlink(str_serverPath, os.path.join(str_clientPath, str_serverNode))
                b_symlink         = True
            except BaseException as e:
                d_ret['status'] = False
                d_ret['msg']    = str(e)
                b_symlink       = False

        d_ret['source']         = str_serverPath
        d_ret['destination']    = str_clientPath
        d_ret['copytree']       = b_copyTree
        d_ret['copyfile']       = b_copyFile
        d_ret['symlink']        = b_symlink
        d_ret['timestamp']      = '%s' % datetime.datetime.now()

        self.ret_client(d_ret)

        return d_ret

    def log_message(self, format, *args):
        """
        This silences the server from spewing to stdout!
        """
        return

    def do_GET(self):
        isAuthorized, error = self.authorizeRequest()
        if isAuthorized:
            return self.execute_GET()
        else:
            self.denyAuth()


    def authorizeRequest(self):
        # Authenticate user request if the server is started with the __b_tokenAuth private flag set to true
        if self.__b_tokenAuth:
            print('Authorizing client request...')
            isAuthorized, error = self.__auth.authorizeClientRequest(self.headers)
            if isAuthorized:
                return (True, "")
            else:
                code, msg, explain = error
                self.send_response(code, msg)
                return (False, "%s %s %s" % (code, msg, explain))

        # If not configured to authorize requests, allow all requests through
        else:
            return (True, "")

    def denyAuth(self):
        d_ret = {
                "message": "Unauthorized Client Request",
                "error": error,
                'status': False
                }

        self.send_error(401)
        self.end_headers()

        self.ret_client(d_ret)
        self.dp.qprint(d_ret, comms = 'tx')
        return d_ret

    def execute_GET(self):
        d_server            = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(self.path).query))
        d_meta              = ast.literal_eval(d_server['meta'])

        d_msg               = {
                                'action':   d_server['action'],
                                'meta':     d_meta
                            }
        d_transport         = d_meta['transport']

        self.dp.qprint(self.path, comms = 'rx')

        if 'checkRemote'    in d_transport and d_transport['checkRemote']:
            self.dp.qprint('Getting status on server filesystem...', comms = 'status')
            d_ret = self.do_GET_remoteStatus(d_msg)
            return d_ret

        if 'compress'       in d_transport:
            d_ret = self.do_GET_withCompression(d_msg)
            return d_ret

        if 'copy'           in d_transport :
            if Gd_internalvar['b_swiftStorage']:
                d_ret = self.do_GET_withCompression(d_msg)
                return d_ret               
            else:
                d_ret = self.do_GET_withCopy(d_msg)
                return d_ret

    def form_get(self, str_verb, data):
        """
        Returns a form from cgi.FieldStorage
        """
        return cgi.FieldStorage(
            IO(data),
            headers = self.headers,
            environ =
            {
                'REQUEST_METHOD':   str_verb,
                'CONTENT_TYPE':     self.headers['Content-Type'],
            }
        )

    def storage_resolveBasedOnKey(self, *args, **kwargs):
        """
        Associate a 'key' text string to an actual storage location in the filesystem space
        on which this service has been launched.

        :param args:
        :param kwargs:
        :return:
        """
        global Gd_internalvar
        str_key     = ""
        b_status    = False

        for k,v in kwargs.items():
            if k == 'key':  str_key = v

        if len(str_key):
            str_internalLocation    = os.path.join('%s/key-%s' %(Gd_internalvar['storeBase'], str_key),'')
            Gd_internalvar['key2address'][str_key]  = str_internalLocation
            b_status                = True

        return {
            'status':   b_status,
            'path':     str_internalLocation
        }

    def internalctl_varprocess(self, *args, **kwargs):
        """

        get/set a specific variable as parsed from the meta JSON.

        :param args:
        :param kwargs:
        :return:
        """
        global Gd_internalvar
        d_meta      = {}
        d_ret       = {}
        str_var     = ''
        b_status    = False

        for k,v in kwargs.items():
            if k == 'd_meta':   d_meta  = v

        str_var     = d_meta['var']

        if d_meta:
            if 'get' in d_meta.keys():
                d_ret[str_var]          = Gd_internalvar[str_var]
                b_status                = True

            if 'set' in d_meta.keys():
                Gd_internalvar[str_var] = d_meta['set']
                d_ret[str_var]          = d_meta['set']
                b_status                = True

            if 'compute' in d_meta.keys() and str_var == 'key2address':
                d_path                  = self.storage_resolveBasedOnKey(key = d_meta['compute'])
                d_ret[str_var]          = d_path['path']
                b_status                = d_path['status']

        return {'d_ret':    d_ret,
                'status':   b_status}

    def internalctl_process(self, *args, **kwargs):
        """

        Process the 'internalctl' action.

             {  "action": "internalctl",
                     "meta": {
                            "var":              "<internalVar>",
                            "set":              "/some/new/path"
                     }
             }

             {  "action": "internalctl",
                     "meta": {
                            "var":              "<internalVar>",
                            "get":              "currentPath"
                     }
             }

             {  "action": "internalctl",
                     "meta": {
                            "var":              "key2address",
                            "compute":          "<keyToken>"
                     }
             }


        <internalVar>: <meta actions>

            * storeBase:    get/set
            * key:          get/set
            * storeAddress: get/compute


        :param args:
        :param kwargs:
        :return:
        """

        d_request           = {}
        b_status            = False
        d_ret               = {
            'status':   b_status
        }

        for k,v in kwargs.items():
            if k == 'request':   d_request   = v
        if d_request:
            d_meta  = d_request['meta']
            d_ret   = self.internalctl_varprocess(d_meta = d_meta)
        return d_ret

    def hello_process(self, *args, **kwargs):
        """

        The 'hello' action is merely to 'speak' with the server. The server
        can return current date/time, echo back a string, query the startup
        command line args, etc.

        This method is a simple means of checking if the server is "up" and
        running.

        :param args:
        :param kwargs:
        :return:
        """

        global Gd_internalvar
        self.dp.qprint("hello_process()", comms = 'status')
        b_status            = False
        d_ret               = {}
        d_request           = {}
        for k, v in kwargs.items():
            if k == 'request':      d_request   = v

        d_meta  = d_request['meta']
        if 'askAbout' in d_meta.keys():
            str_askAbout        = d_meta['askAbout']
            d_ret['name']       = Gd_internalvar['name']
            d_ret['version']    = Gd_internalvar['version']
            if str_askAbout == 'timestamp':
                str_timeStamp   = datetime.datetime.today().strftime('%Y%m%d%H%M%S.%f')
                d_ret['timestamp']              = {}
                d_ret['timestamp']['now']       = str_timeStamp
                b_status                        = True
            if str_askAbout == 'sysinfo':
                d_ret['sysinfo']                = {}
                d_ret['sysinfo']['system']      = platform.system()
                d_ret['sysinfo']['machine']     = platform.machine()
                d_ret['sysinfo']['platform']    = platform.platform()
                d_ret['sysinfo']['uname']       = platform.uname()
                d_ret['sysinfo']['version']     = platform.version()
                d_ret['sysinfo']['memory']      = psutil.virtual_memory()
                d_ret['sysinfo']['cpucount']    = multiprocessing.cpu_count()
                d_ret['sysinfo']['loadavg']     = os.getloadavg()
                d_ret['sysinfo']['cpu_percent'] = psutil.cpu_percent()
                d_ret['sysinfo']['hostname']    = socket.gethostname()
                d_ret['sysinfo']['inet']        = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]
                b_status                        = True
            if str_askAbout == 'echoBack':
                d_ret['echoBack']               = {}
                d_ret['echoBack']['msg']        = d_meta['echoBack']
                b_status                        = True
        
        self.send_response(200)
        self.end_headers()

        d_ret['User-agent'] = self.headers['user-agent']

        return { 'stdout': { 
                            'd_ret':   d_ret,
                            'status':  b_status
                            }
        }

    def rmtree_process(self, **kwargs):
        """
        Remove (if possible) a directory location either specified directly
        with a "path" or indirectly with a "key".

        """
        str_path    = ''
        str_msg     = ''
        b_status    = False
        d_msg       = {}
        d_ret       = {}
        for k,v in kwargs.items():
            if k == 'request':  d_msg   = v

        d_meta      = d_msg['meta']
        str_path    = self.remoteLocation_resolve(d_meta)['path']
        if len(str_path):
            # str_path    = d_meta['path']
            self.dp.qprint('Will rmtree <%s>; UID %s, eUID %s...' % (str_path, os.getuid(), os.getegid()))
            try:
                shutil.rmtree(str_path)
                b_status    = True
                str_msg     = 'Successfully removed tree %s' % str_path
                self.dp.qprint(str_msg, comms = 'status')
            except:
                b_status    = False
                str_msg     = 'Could not remove tree %s. Possible permission error or invalid path. Try using action `ls`' % str_path
                self.dp.qprint(str_msg, comms = 'error')
        d_ret   = {
            'status':   b_status,
            'msg':      str_msg
        }

        return d_ret

    def ls_process(self, **kwargs):
        """
        Return a list of dictionary entries of directory entries of 
        path or key store.
        """

        str_path    = ''
        str_msg     = ''
        b_status    = False
        d_msg       = {}
        d_ret       = {}
        d_e         = {}
        d_ls        = {}
        for k,v in kwargs.items():
            if k == 'request':  d_msg   = v

        d_meta      = d_msg['meta']
        str_path    = self.remoteLocation_resolve(d_meta)['path']
        if 'subdir' in d_meta.keys():
            str_path    = os.path.join(str_path, d_meta['subdir'])
        if len(str_path):
            self.dp.qprint('scandir on  %s...' % str_path)
            try:
                for e in os.scandir(str_path):
                    str_type = ''
                    if e.is_file():     str_type = 'file'
                    if e.is_dir():      str_type = 'dir'
                    if e.is_symlink():  str_type = 'symlink'
                    d_e = {
                        'type':     str_type,
                        'path':     os.path.join(str_path, e.name),
                        'uid':      e.stat().st_uid,
                        'gid':      e.stat().st_gid,
                        'size':     e.stat().st_size,
                        'mtime':    e.stat().st_mtime,
                        'ctime':    e.stat().st_ctime,
                        'atime':    e.stat().st_atime
                    }
                    d_ls[e.name]   = d_e
                b_status    = True
                str_msg     = 'Successful scandir on %s' % str_path
                self.dp.qprint(str_msg, comms = 'status')
            except:
                b_status    = False
                str_msg     = 'Could not scandir >%s<. Possible permission error.' % str_path
                self.dp.qprint(str_msg, comms = 'error')
        d_ret   = {
            'status':   b_status,
            'msg':      str_msg,
            'd_ls':     d_ls
        }

        return d_ret
    
    def getHeaders(self):
        """
        Return headers of the request
        """
        
        self.dp.qprint('headers= %s' %self.headers)
        return self.headers['content-length']     

    def rfileRead(self, length):
        """
        Return the contents of the file transmitted
        """

        return self.rfile.read(int(length))

    def unpackForm(self, form, d_form):
        """
        Load the json request
        """

        self.dp.qprint("Unpacking multi-part form message...", comms = 'status')
        for key in form:
            self.dp.qprint("\tUnpacking field '%s..." % key, comms = 'status')
            d_form[key]     = form.getvalue(key)
        d_msg = json.loads((d_form['d_msg']))

        return d_msg

    def do_POST(self, **kwargs):
        isAuthorized, error = self.authorizeRequest()
        if isAuthorized:
            return self.execute_POST(**kwargs)
        else:
            self.denyAuth()

    def execute_POST(self, **kwargs):
        b_skipInit  = False
        d_msg       = {}
        for k,v in kwargs.items():
            self.dp.qprint('in for ' +  str(k))
            if k == 'd_msg':
                d_msg       = v
                b_skipInit  = True

        if not b_skipInit:
            # Parse the form data posted
            self.dp.qprint(str(self.headers), comms = 'rx')

            length              = self.getHeaders()
            data                = self.rfileRead(length)
            form                = self.form_get('POST', data)
            d_form              = {}
            d_ret               = {
                'msg'      : 'In do_POST',
                'status'   : True,
                'formsize' : sys.getsizeof(form)
            }

            self.dp.qprint('data length = %d' % len(data), comms = 'status')
            self.dp.qprint('form length = %d' % len(form), comms = 'status')

            if len(form):
                d_msg = self.unpackForm(form, d_form)
            else:
                self.dp.qprint("Parsing JSON data...", comms = 'status')
                d_data              = json.loads(data.decode())
                try:
                    d_msg           = d_data['payload']
                except:
                    d_msg           = d_data

        self.dp.qprint('d_msg = %s' % self.pp.pformat(d_msg).strip(), comms = 'status')
        d_meta              = d_msg['meta']

        if 'action' in d_msg:
            self.dp.qprint("verb: %s detected." % d_msg['action'], comms = 'status')
            if 'Path' not in d_msg['action']:
                str_method      = '%s_process' % d_msg['action']
                self.dp.qprint("method to call: %s(request = d_msg) " % str_method, comms = 'status')
                d_done          = {'status': False}
                try:
                    method      = getattr(self, str_method)
                    d_done      = method(request = d_msg)
                except:
                    str_msg     = "Class '{}' does not implement method '{}'".format(self.__class__.__name__, 
                                                                                     str_method)
                    d_done = {
                        'status':   False,
                        'msg':      str_msg
                    }
                    self.dp.qprint(str_msg, comms = 'error')
                self.dp.qprint(self.pp.pformat(d_done).strip(), comms = 'tx')
                d_ret = d_done

        if 'ctl' in d_meta:
            self.do_POST_serverctl(d_meta)

        if 'transport' in d_meta:
            d_transport     = d_meta['transport']
            if 'compress' in d_transport:
                d_ret       = self.do_POST_withCompression(
                    data    = data,
                    length  = length,
                    form    = form,
                    d_form  = d_form 
                )
            if 'copy' in d_transport :
                if Gd_internalvar['b_swiftStorage']:
                    d_ret   = self.do_POST_withCompression(
                    data    = data,
                    length  = length,
                    form    = form,
                    d_form  = d_form
                )
                else:
                    d_ret   = self.do_POST_withCopy(d_meta)


        if not b_skipInit: self.ret_client(d_ret)
        return d_ret

    def do_POST_serverctl(self, d_meta):
        """
        """
        d_ctl               = d_meta['ctl']
        self.dp.qprint('Processing server ctl...', comms = 'status')
        self.dp.qprint(d_meta, comms = 'rx')
        if 'serverCmd' in d_ctl:
            if d_ctl['serverCmd'] == 'quit':
                self.dp.qprint('Shutting down server', comms = 'status')
                d_ret = {
                    'msg':      'Server shut down',
                    'status':   True
                }
                self.dp.qprint(d_ret, comms = 'tx')
                self.ret_client(d_ret)
                os._exit(0)

    def do_POST_withCopy(self, d_meta):
        """
        Process a "POST" using copy operations

        :return:
        """

        d_local             = d_meta['local']
        d_remote            = d_meta['remote']
        d_transport         = d_meta['transport']
        d_copy              = d_transport['copy']

        str_serverPath      = self.remoteLocation_resolve(d_remote)['path']
        str_clientPath      = d_local['path']

        b_copyTree          = False
        b_copyFile          = False

        d_ret               = {'status': True}

        if not d_copy['symlink']:
            if os.path.isdir(str_clientPath):
                b_copyTree      = True
                str_clientNode  = str_clientPath.split('/')[-1]
                try:
                    shutil.copytree(str_clientPath, os.path.join(str_serverPath, str_clientNode))
                except BaseException as e:
                    d_ret['status'] = False
                    d_ret['msg']    = str(e)
            if os.path.isfile(str_clientPath):
                b_copyFile      = True
                shutil.copy2(str_clientPath, str_serverPath)
            d_ret['copytree']       = b_copyTree
            d_ret['copyfile']       = b_copyFile

        if d_copy['symlink']:
            str_clientNode  = str_clientPath.split('/')[-1]
            try:
                os.symlink(str_clientPath, os.path.join(str_serverPath, str_clientNode))
            except BaseException as e:
                d_ret['status'] = False
                d_ret['msg']    = str(e)
            d_ret['symlink']    = 'ln -s %s %s' % (str_clientPath, str_serverPath)

        # d_ret['d_meta']         = d_meta
        d_ret['source']         = str_clientPath
        d_ret['destination']    = str_serverPath
        d_ret['copytree']       = b_copyTree
        d_ret['copyfile']       = b_copyFile
        d_ret['timestamp']      = '%s' % datetime.datetime.now()

        # self.ret_client(d_ret)

        return d_ret

    def do_GET_preop(self, **kwargs):
        """
        Perform any pre-operations relating to a "PULL" or "GET" request.

        Essentially, for the 'plugin' case, this means appending a string
        'outgoing' to the remote storage location path and create that dir!

        """

        d_meta          = {}
        d_postop        = {}
        d_ret           = {}
        b_status        = False
        str_path        = ''
        for k,v in kwargs.items():
            if k == 'meta':         d_meta          = v
            if k == 'path':         str_path        = v

        if 'specialHandling' in d_meta:
            d_preop = d_meta['specialHandling']
            if 'cmd' in d_preop.keys():
                str_cmd     = d_postop['cmd']
                str_keyPath = ''
                if 'remote' in d_meta.keys():
                    str_keyPath = self.remoteLocation_resolve(d_meta['remote'])['path']
                str_cmd     = str_cmd.replace('%key', str_keyPath)
                b_status    = True
                d_ret['cmd']    = str_cmd
            if 'op' in d_preop.keys():
                if d_preop['op']   == 'plugin':
                    str_outgoingPath        = '%s/outgoing' % str_path
                    d_ret['op']             = 'plugin'
                    d_ret['outgoingPath']   = str_outgoingPath
                    b_status                = True

        d_ret['status']     = b_status
        d_ret['timestamp']  = '%s' % datetime.datetime.now()
        return d_ret

    def ls_do(self, **kwargs):
        """
        Perform an ls based on the passed args.
        """
        for k,v in kwargs.items():
            if k == 'meta':         d_meta          = v

        if 'remote' in d_meta.keys():
            d_remote = d_meta['remote']
            for subdir in ['incoming', 'outgoing']:
                d_remote['subdir']  = subdir                    
                dmsg_lstree = { 
                                'action': 'rmtree',
                                'meta'  :  d_remote
                                }
                d_ls                    = self.ls_process(    request = dmsg_lstree)
                self.dp.qprint("target ls = \n%s" % self.pp.pformat(d_ls).strip())

    def do_GET_postop(self, **kwargs):
        """
        Perform any post-operations relating to a "GET" / "PULL" request.

        :param kwargs:
        :return:
        """

        str_cmd         = ''
        d_meta          = {}
        d_postop        = {}
        d_ret           = {}
        b_status        = False
        str_path        = ''

        for k,v in kwargs.items():
            if k == 'meta':         d_meta          = v

        if 'specialHandling' in d_meta:
            d_postop = d_meta['specialHandling']
            if 'cleanup' in d_postop.keys():
                if d_postop['cleanup']:
                    #
                    # In this case we remove the 'remote' path or key lookup:
                    #
                    #   mv $str_path /tmp/$str_path
                    #   mkdir $str_path
                    #   mv /tmp/$str_path $str_path/incoming
                    #
                    if 'remote' in d_meta.keys():
                        d_remote = d_meta['remote']
                    self.ls_do(meta = d_meta)
                    dmsg_rmtree = { 
                                    'action': 'rmtree',
                                    'meta'  :  d_remote
                                    }
                    self.dp.qprint("Performing GET postop cleanup", comms = 'status')
                    self.dp.qprint("dmsg_rmtree: %s" % dmsg_rmtree, comms = 'status')
                    d_ret['rmtree']         = self.rmtree_process(request = dmsg_rmtree)
                    d_ret['op']             = 'plugin'
                    b_status                = d_ret['rmtree']['status']

        d_ret['status']     = b_status
        d_ret['timestamp']  = '%s' % datetime.datetime.now()
        return d_ret

    def do_POST_postop(self, **kwargs):
        """
        Perform any post-operations relating to a "POST" request.

        :param kwargs:
        :return:
        """

        str_cmd         = ''
        d_meta          = {}
        d_postop        = {}
        d_ret           = {}
        b_status        = False
        str_path        = ''

        for k,v in kwargs.items():
            if k == 'meta':         d_meta          = v
            if k == 'path':         str_path        = v

        if 'specialHandling' in d_meta:
            d_postop = d_meta['specialHandling']
            if 'cmd' in d_postop.keys():
                str_cmd     = d_postop['cmd']
                str_keyPath = ''
                if 'remote' in d_meta.keys():
                    str_keyPath = self.remoteLocation_resolve(d_meta['remote'])['path']
                str_cmd     = str_cmd.replace('%key', str_keyPath)
                b_status    = True
                d_ret['cmd']    = str_cmd
            if 'op' in d_postop.keys():
                if d_postop['op']   == 'plugin':
                    #
                    # In this case the contents of the keyStore need to be moved to a 
                    # directory called 'incoming' within that store. In shell, this 
                    # would amount to:
                    #
                    #   mv $str_path /tmp/$str_path
                    #   mkdir $str_path
                    #   mv /tmp/$str_path $str_path/incoming
                    #
                    str_uuid            = '%s' % uuid.uuid4()
                    str_tmp             = os.path.join('/tmp', str_uuid)
                    str_incomingPath    = os.path.join(str_path, 'incoming')
                    str_outgoingPath    = os.path.join(str_path, 'outgoing')
                    self.dp.qprint("Moving %s to %s..." % (str_path, str_tmp))
                    shutil.move(str_path, str_tmp)
                    self.dp.qprint("Recreating clean path %s..." % str_path)
                    os.makedirs(str_path)
                    st = os.stat(str_path)
                    os.chmod(str_path, stat.S_IRWXO | stat.S_IRWXG | stat.S_IRWXU)
                    self.dp.qprint("Moving %s to %s" % (str_tmp, str_incomingPath))
                    shutil.move(str_tmp, str_incomingPath)

                    d_ret['op']             = 'plugin'
                    d_ret['shareDir']       = str_path
                    d_ret['tmpPath']        = str_tmp
                    d_ret['incomingPath']   = str_incomingPath
                    d_ret['outgoingPath']   = str_outgoingPath
                    os.makedirs(str_outgoingPath)
                    st = os.stat(str_outgoingPath)
                    os.chmod(str_outgoingPath, stat.S_IRWXO | stat.S_IRWXG | stat.S_IRWXU)
                    b_status                = True

        d_ret['status']     = b_status
        d_ret['timestamp']  = '%s' % datetime.datetime.now()
        return d_ret

    def do_POST_withCompression(self, **kwargs):

        # Parse the form data posted

        self.dp.qprint(str(self.headers),              comms = 'rx')
        self.dp.qprint('do_POST_withCompression()',    comms = 'status')

        # data    = None
        # length  = 0
        # form    = None
        d_form  = {}
        d_ret   = {}

        for k,v in kwargs.items():
            # if k == 'data':     data    = v
            # if k == 'length':   length  = v
            # if k == 'form':     form    = v
            if k == 'd_form':   d_form  = v

        d_msg               = json.loads((d_form['d_msg']))
        d_meta              = d_msg['meta']
        # d_meta              = json.loads(d_form['d_meta'])
        fileContent         = d_form['local']
        
        str_fileName        = d_meta['local']['path']

        d_remote            = d_meta['remote']
        b_unpack            = False
        # b_serverPath        = False
        # str_unpackBase      = self.server.str_fileBase

        str_unpackPath      = self.remoteLocation_resolve(d_remote)['path']
        str_unpackBase      = os.path.join(str_unpackPath,'')
        d_transport         = d_meta['transport']
        d_compress          = d_transport['compress']
        if 'unpack' in d_compress:
            b_unpack        = d_compress['unpack']

        str_fileOnly        = os.path.split(str_fileName)[-1]
        str_fileSuffix      = ""
        if d_compress['archive'] == "zip":
            str_fileSuffix = ".zip"

        str_localFile   = "%s%s%s" % (str_unpackBase, str_fileOnly, str_fileSuffix)
        
        #Decoding 
        d_ret['write']   = {}

        try:
            data = fileContent.decode()
            d_ret['write']['decode'] = True
        except Exception as err:
            d_ret['write']['decode'] = False
            data = fileContent

        b_zip = b_unpack and (d_compress['archive'] == 'zip')

        d_ret= self.storeData(file_name= str_localFile, client_path = str_fileName,
                              file_content= data, Path= str_unpackPath, is_zip=b_zip,d_ret=d_ret)
        
        d_ret['postop'] = self.do_POST_postop(meta          = d_meta,
                                              path          = str_unpackPath)


        self.send_response(200)
        self.end_headers()

        d_ret['User-agent'] = self.headers['user-agent']

        # self.ret_client(d_ret)
        self.dp.qprint(self.pp.pformat(d_ret).strip(), comms = 'tx')

        return d_ret

    def storeData(self, **kwargs):
        raise NotImplementedError('Abstract Method: Please implement this method in child class')

    def ret_client(self, d_ret):
        """
        Simply "writes" the d_ret using json and the client wfile.

        :param d_ret:
        :return:
        """
        global Gd_internalvar
        if not Gd_internalvar['httpResponse']:
            self.wfile.write(json.dumps(d_ret).encode())
        else:
            self.wfile.write(str(Response(json.dumps(d_ret))).encode())


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """
    Handle requests in a separate thread.
    """

    def col2_print(self, str_left, str_right, level = 1):
        self.dp.qprint(Colors.WHITE +
              ('%*s' % (self.LC, str_left)), 
              end       = '', 
              level     = level,
              syslog    = False)
        self.dp.qprint(Colors.LIGHT_BLUE +
              ('%*s' % (self.RC, str_right)) + Colors.NO_COLOUR, 
              level     = level,
              syslog    = False)

    def __init__(self, *args, **kwargs):
        """

        Holder for constructor of class -- allows for explicit setting
        of member 'self' variables.

        :return:
        """

        HTTPServer.__init__(self, *args, **kwargs)
        self.LC                                 = 40
        self.RC                                 = 40
        self.args                               = None
        self.str_desc                           = 'pfioh'
        self.str_name                           = self.str_desc
        self.str_version                        = ""
        self.str_fileBase                       = "received-"
        self.str_storeBase                      = ""
        self.b_createDirsAsNeeded               = False
        self.b_swiftStorage                     = False

        self.str_unpackDir                      = "/tmp/unpack"
        self.b_removeZip                        = False

    def setup(self, **kwargs):
        global Gd_internalvar
        for k,v in kwargs.items():
            if k == 'args': self.args           = v
            if k == 'desc': self.str_desc       = v
            if k == 'ver':  self.str_version    = v

        self.str_fileBase                       = "received-"
        self.str_storeBase                      = self.args['storeBase']
        self.b_createDirsAsNeeded               = self.args['b_createDirsAsNeeded']

        self.str_unpackDir                      = self.args['storeBase']
        self.b_removeZip                        = False
        self.b_swiftStorage                     = self.args['b_swiftStorage']


        Gd_internalvar['httpResponse']          = self.args['b_httpResponse']
        Gd_internalvar['name']                  = self.str_name
        Gd_internalvar['version']               = self.str_version
        Gd_internalvar['createDirsAsNeeded']    = self.args['b_createDirsAsNeeded']
        Gd_internalvar['storeBase']             = self.args['storeBase']
        Gd_internalvar['b_swiftStorage']        = self.args['b_swiftStorage']
        Gd_internalvar['verbosity']             = int(self.args['verbosity'])

        self.verbosity                          = Gd_internalvar['verbosity']

        self.dp                                 = debug(verbosity = self.verbosity)

        self.dp.qprint(self.str_desc)
        if self.args['b_tokenAuth']:
            Gd_internalvar['b_tokenAuth'] = True
            if self.args['str_tokenPath'] != '':
                Gd_internalvar['authModule']        = Auth('http', self.args['str_tokenPath'])
            else:
                Gd_internalvar['authModule']        = Auth('http', 'pfioh_config.cfg')
        print(self.str_desc)

        self.col2_print("Listening on address:",    self.args['ip'])
        self.col2_print("Listening on port:",       self.args['port'])
        self.col2_print("Server listen forever:",   self.args['b_forever'])
        self.col2_print("Return HTTP responses:",   self.args['b_httpResponse'])
        self.col2_print("Authorization enabled:",   self.args['b_tokenAuth'])

        self.dp.qprint(
                Colors.BLINK_GREEN + 
                "\n\n\t\t\t\tWaiting for incoming data...\n\n" + 
                Colors.NO_COLOUR, 
                flush   = True,
                syslog  = False
        )


def zipdir(path, ziph, **kwargs):
    """
    Zip up a directory.

    :param path:
    :param ziph:
    :param kwargs:
    :return:
    """
    str_arcroot = ""
    for k, v in kwargs.items():
        if k == 'arcroot':  str_arcroot = v

    for root, dirs, files in os.walk(path):
        for file in files:
            str_arcfile = os.path.join(root, file)
            if len(str_arcroot):
                str_arcname = str_arcroot.split('/')[-1] + str_arcfile.split(str_arcroot)[1]
            else:
                str_arcname = str_arcfile
            try:
                ziph.write(str_arcfile, arcname = str_arcname)
            except:
                print("Skipping %s" % str_arcfile)


def zip_process(**kwargs):
    """
    Process zip operations.

    :param kwargs:
    :return:
    """

    str_localPath   = ""
    str_zipFileName = ""
    str_action      = "zip"
    str_arcroot     = ""
    for k,v in kwargs.items():
        if k == 'path':             str_localPath   = v
        if k == 'action':           str_action      = v
        if k == 'payloadFile':      str_zipFileName = v
        if k == 'arcroot':          str_arcroot     = v

    if str_action       == 'zip':
        str_mode        = 'w'
        str_arcFileName = '%s/%s' % (tempfile.gettempdir(), uuid.uuid4())
        str_zipFileName = str_arcFileName + '.zip'
    else:
        str_mode        = 'r'

    ziphandler          = zipfile.ZipFile(str_zipFileName, str_mode, zipfile.ZIP_DEFLATED)
    if str_mode == 'w':
        if os.path.isdir(str_localPath):
            zipdir(str_localPath, ziphandler, arcroot = str_arcroot)
            # str_zipFileName = shutil.make_archive(str_arcFileName, 'zip', str_localPath)
        else:
            if len(str_arcroot):
                str_arcname = str_arcroot.split('/')[-1] + str_localPath.split(str_arcroot)[1]
            else:
                str_arcname = str_localPath
            try:
                ziphandler.write(str_localPath, arcname = str_arcname)
            except:
                ziphandler.close()
                os.remove(str_zipFileName)
                return {
                    'msg':      json.dumps({"msg": "No file or directory found for '%s'" % str_localPath}),
                    'status':   False
                }
    if str_mode     == 'r':
        ziphandler.extractall(str_localPath)
    ziphandler.close()
    return {
        'msg':              '%s operation successful' % str_action,
        'fileProcessed':    str_zipFileName,
        'status':           True,
        'path':             str_localPath,
        'zipmode':          str_mode,
        'filesize':         "{:,}".format(os.stat(str_zipFileName).st_size),
        'timestamp':        '%s' % datetime.datetime.now()
    }


def base64_process(**kwargs):
    """
    Process base64 file io
    """

    str_fileToSave      = ""
    str_fileToRead      = ""
    str_action          = "encode"
    data                = None

    for k,v in kwargs.items():
        if k == 'action':           str_action          = v
        if k == 'payloadBytes':     data                = v
        if k == 'payloadFile':      str_fileToRead      = v
        if k == 'saveToFile':       str_fileToSave      = v
        # if k == 'sourcePath':       str_sourcePath      = v

    if str_action       == "encode":
        # Encode the contents of the file at targetPath as ASCII for transmission
        if len(str_fileToRead):
            with open(str_fileToRead, 'rb') as f:
                data            = f.read()
                f.close()
        data_b64            = base64.b64encode(data)
        with open(str_fileToSave, 'wb') as f:
            f.write(data_b64)
            f.close()
        return {
            'msg':              'Encode successful',
            'fileProcessed':    str_fileToSave,
            'status':           True
            # 'encodedBytes':     data_b64
        }

    if str_action       == "decode":
        if len(data) % 4:
            # not a multiple of 4, add padding:
            data += '=' * (4 - len(data) % 4)
        bytes_decoded     = base64.b64decode(data)
        with open(str_fileToSave, 'wb') as f:
            f.write(bytes_decoded)
            f.close()
        return {
            'msg':              'Decode successful',
            'fileProcessed':    str_fileToSave,
            'status':           True
            # 'decodedBytes':     bytes_decoded
        }
