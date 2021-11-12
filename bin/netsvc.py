#!/usr/bin/env python
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    The refactoring about the OpenSSL support come from Tryton
#    Copyright (C) 2007-2009 Cédric Krier.
#    Copyright (C) 2007-2009 Bertrand Chenal.
#    Copyright (C) 2008 B2CK SPRL.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import SimpleXMLRPCServer
import SocketServer
import logging
import logging.handlers
import os
import signal
import socket
import select
import errno
import sys
import threading
import time
import xmlrpclib
import release
from pprint import pformat
import heapq

SERVICES = {}
GROUPS = {}

class Service(object):
    def __init__(self, name, audience=''):
        SERVICES[name] = self
        self.__name = name
        self._methods = {}

    def joinGroup(self, name):
        GROUPS.setdefault(name, {})[self.__name] = self

    def exportMethod(self, method):
        if callable(method):
            self._methods[method.__name__] = method

    def abortResponse(self, error, description, origin, details):
        if not tools.config['debug_mode']:
            raise Exception("%s -- %s\n\n%s"%(origin, description, details))
        else:
            raise

class LocalService(Service):
    def __init__(self, name):
        self.__name = name
        try:
            self._service = SERVICES[name]
            for method_name, method_definition in self._service._methods.items():
                setattr(self, method_name, method_definition)
        except KeyError, keyError:
            Logger().notifyChannel('module', LOG_ERROR, 'This service does not exists: %s' % (str(keyError),) )
            raise
    def __call__(self, method, *params):
        return getattr(self, method)(*params)

def service_exist(name):
    return SERVICES.get(name, False)

LOG_NOTSET = 'notset'
LOG_DEBUG_RPC = 'debug_rpc'
LOG_DEBUG = 'debug'
LOG_INFO = 'info'
LOG_WARNING = 'warn'
LOG_ERROR = 'error'
LOG_CRITICAL = 'critical'

# add new log level below DEBUG
logging.DEBUG_RPC = logging.DEBUG - 1


class DBLogger(logging.getLoggerClass()):
    def makeRecord(self, *args, **kwargs):
        record = logging.Logger.makeRecord(self, *args, **kwargs)
        record.dbname = getattr(threading.currentThread(), 'dbname', '?')
        return record

def init_logger():
    import os
    from tools.translate import resetlocale
    resetlocale()

    logging.setLoggerClass(DBLogger)

    # create a format for log messages and dates
    formatter = logging.Formatter('[%(asctime)s][%(dbname)s] %(levelname)s:%(name)s:%(message)s')

    logging_to_stdout = False
    if tools.config['syslog']:
        # SysLog Handler
        if os.name == 'nt':
            handler = logging.handlers.NTEventLogHandler("%s %s" %
                                                         (release.description,
                                                          release.version))
        else:
            handler = logging.handlers.SysLogHandler('/dev/log')
        formatter = logging.Formatter("%s %s" % (release.description, release.version) + ':%(dbname)s:%(levelname)s:%(name)s:%(message)s')

    elif tools.config['logfile']:
        # LogFile Handler
        logf = tools.config['logfile']
        try:
            dirname = os.path.dirname(logf)
            if dirname and not os.path.isdir(dirname):
                os.makedirs(dirname)
            handler = logging.handlers.TimedRotatingFileHandler(logf,'D',1,30)
        except Exception, ex:
            sys.stderr.write("ERROR: couldn't create the logfile directory. Logging to the standard output.\n")
            handler = logging.StreamHandler(sys.stdout)
            logging_to_stdout = True
    else:
        # Normal Handler on standard output
        handler = logging.StreamHandler(sys.stdout)
        logging_to_stdout = True


    # tell the handler to use this format
    handler.setFormatter(formatter)

    # add the handler to the root logger
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(tools.config['log_level'] or '0')

    if logging_to_stdout and os.name != 'nt':
        # change color of level names
        # uses of ANSI color codes
        # see http://pueblo.sourceforge.net/doc/manual/ansi_color_codes.html
        # maybe use http://code.activestate.com/recipes/574451/
        colors = ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', None, 'default']
        foreground = lambda f: 30 + colors.index(f)
        background = lambda f: 40 + colors.index(f)

        mapping = {
            'DEBUG_RPC': ('blue', 'white'),
            'DEBUG': ('blue', 'default'),
            'INFO': ('green', 'default'),
            'WARNING': ('yellow', 'default'),
            'ERROR': ('red', 'default'),
            'CRITICAL': ('white', 'red'),
        }

        for level, (fg, bg) in mapping.items():
            msg = "\x1b[%dm\x1b[%dm%s\x1b[0m" % (foreground(fg), background(bg), level)
            logging.addLevelName(getattr(logging, level), msg)


class Logger(object):

    def notifyChannel(self, name, level, msg):
        from service.web_services import common

        log = logging.getLogger(tools.ustr(name))

        if level == LOG_DEBUG_RPC and not hasattr(log, level):
            fct = lambda msg, *args, **kwargs: log.log(logging.DEBUG_RPC, msg, *args, **kwargs)
            setattr(log, LOG_DEBUG_RPC, fct)

        level_method = getattr(log, level)

        if isinstance(msg, Exception):
            msg = tools.exception_to_unicode(msg)

        msg = tools.ustr(msg).strip()

        if level in (LOG_ERROR,LOG_CRITICAL):
            msg = common().get_server_environment() + '\n' + msg

        result = msg.split('\n')
        if len(result)>1:
            for idx, s in enumerate(result):
                level_method('[%02d]: %s' % (idx+1, s,))
        elif result:
            level_method(result[0])

    def shutdown(self):
        logging.shutdown()

import tools
init_logger()

class Agent(object):
    """Singleton that keeps track of cancellable tasks to run at a given
       timestamp.
       The tasks are caracterised by:
            * a timestamp
            * the database on which the task run
            * the function to call
            * the arguments and keyword arguments to pass to the function

        Implementation details:
          Tasks are stored as list, allowing the cancellation by setting
          the timestamp to 0.
          A heapq is used to store tasks, so we don't need to sort
          tasks ourself.
    """
    __tasks = []
    __tasks_by_db = {}
    _logger = Logger()

    @classmethod
    def setAlarm(cls, function, timestamp, db_name, *args, **kwargs):
        task = [timestamp, db_name, function, args, kwargs]
        heapq.heappush(cls.__tasks, task)
        cls.__tasks_by_db.setdefault(db_name, []).append(task)

    @classmethod
    def cancel(cls, db_name):
        """Cancel all tasks for a given database. If None is passed, all tasks are cancelled"""
        if db_name is None:
            cls.__tasks, cls.__tasks_by_db = [], {}
        else:
            if db_name in cls.__tasks_by_db:
                for task in cls.__tasks_by_db[db_name]:
                    task[0] = 0

    @classmethod
    def quit(cls):
        cls.cancel(None)

    @classmethod
    def runner(cls):
        """Neverending function (intended to be ran in a dedicated thread) that
           checks every 60 seconds tasks to run.
        """
        current_thread = threading.currentThread()
        while True:
            while cls.__tasks and cls.__tasks[0][0] < time.time():
                task = heapq.heappop(cls.__tasks)
                timestamp, dbname, function, args, kwargs = task
                cls.__tasks_by_db[dbname].remove(task)
                if not timestamp:
                    # null timestamp -> cancelled task
                    continue
                current_thread.dbname = dbname   # hack hack
                cls._logger.notifyChannel('timers', LOG_DEBUG, "Run %s.%s(*%r, **%r)" % (function.im_class.__name__, function.func_name, args, kwargs))
                delattr(current_thread, 'dbname')
                task_thread = threading.Thread(target=function, name='netsvc.Agent.task', args=args, kwargs=kwargs)
                # force non-daemon task threads (the runner thread must be daemon, and this property is inherited by default)
                task_thread.daemon = False
                task_thread.start()
                time.sleep(1)
            time.sleep(60)

agent_runner = threading.Thread(target=Agent.runner, name="netsvc.Agent.runner")
# the agent runner is a typical daemon thread, that will never quit and must be
# terminated when the main process exits - with no consequence (the processing
# threads it spawns are not marked daemon)
agent_runner.daemon = True
agent_runner.start()


import traceback

class xmlrpc(object):
    class RpcGateway(object):
        def __init__(self, name):
            self.name = name

class OpenERPDispatcherException(Exception):
    def __init__(self, exception, traceback):
        self.exception = exception
        self.traceback = traceback

class OpenERPDispatcher:
    def log(self, title, msg):
        if tools.config['log_level'] == logging.DEBUG_RPC:
            Logger().notifyChannel('%s' % title, LOG_DEBUG_RPC, pformat(msg))

    def dispatch(self, service_name, method, params):
        if service_name not in GROUPS['web-services']:
            raise Exception('AccessDenied')
        try:
            self.log('service', service_name)
            self.log('method', method)
            self.log('params', params)
            result = LocalService(service_name)(method, *params)
            if result is None: #we cannot marshal none in XMLRPC
                result = False
            self.log('result', result)
            return result
        except Exception, e:
            self.log('exception', tools.exception_to_unicode(e))
            if hasattr(e, 'traceback'):
                tb = e.traceback
            else:
                tb = sys.exc_info()
            tb_s = "".join(traceback.format_exception(*tb))
            if tools.config['debug_mode']:
                import pdb
                pdb.post_mortem(tb[2])
            raise OpenERPDispatcherException(e, tb_s)

class GenericXMLRPCRequestHandler(OpenERPDispatcher):
    def _dispatch(self, method, params):
        try:
            service_name = self.path.split("/")[-1]
            return self.dispatch(service_name, method, params)
        except OpenERPDispatcherException, e:
            raise xmlrpclib.Fault(tools.exception_to_unicode(e.exception), e.traceback)

class SSLSocket(object):
    def __init__(self, socket):
        if not hasattr(socket, 'sock_shutdown'):
            from OpenSSL import SSL
            ctx = SSL.Context(SSL.SSLv23_METHOD)
            ctx.use_privatekey_file(tools.config['secure_pkey_file'])
            ctx.use_certificate_file(tools.config['secure_cert_file'])
            self.socket = SSL.Connection(ctx, socket)
        else:
            self.socket = socket

    def shutdown(self, how):
        return self.socket.sock_shutdown(how)

    def __getattr__(self, name):
        return getattr(self.socket, name)

class SimpleXMLRPCRequestHandler(GenericXMLRPCRequestHandler, SimpleXMLRPCServer.SimpleXMLRPCRequestHandler):
    rpc_paths = map(lambda s: '/xmlrpc/%s' % s, GROUPS.get('web-services', {}).keys())

class SecureXMLRPCRequestHandler(SimpleXMLRPCRequestHandler):
    def setup(self):
        self.connection = SSLSocket(self.request)
        self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
        self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)

class SimpleThreadedXMLRPCServer(SocketServer.ThreadingMixIn, SimpleXMLRPCServer.SimpleXMLRPCServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        SimpleXMLRPCServer.SimpleXMLRPCServer.server_bind(self)

class SecureThreadedXMLRPCServer(SimpleThreadedXMLRPCServer):
    def __init__(self, server_address, HandlerClass, logRequests=1):
        SimpleThreadedXMLRPCServer.__init__(self, server_address, HandlerClass, logRequests)
        self.socket = SSLSocket(socket.socket(self.address_family, self.socket_type))
        self.server_bind()
        self.server_activate()


def _close_socket(sock):
    if os.name != 'nt':     # XXX if someone know why, please leave a comment.
        try:
            sock.shutdown(getattr(socket, 'SHUT_RDWR', 2))
        except socket.error, e:
            if e.errno != errno.ENOTCONN: raise
            # OSX, socket shutdowns both sides if any side closes it
            # causing an error 57 'Socket is not connected' on shutdown
            # of the other side (or something), see
            # http://bugs.python.org/issue4397
            Logger().notifyChannel(
                'server', LOG_DEBUG,
                '"%s" when shutting down server socket, '
                'this is normal under OS X'%e)
    sock.close()


class HttpDaemon(threading.Thread):
    def __init__(self, interface, port, secure=False):
        threading.Thread.__init__(self)
        self.__port = port
        self.__interface = interface
        self.secure = bool(secure)
        handler_class = (SimpleXMLRPCRequestHandler, SecureXMLRPCRequestHandler)[self.secure]
        server_class = (SimpleThreadedXMLRPCServer, SecureThreadedXMLRPCServer)[self.secure]

        if self.secure:
            from OpenSSL.SSL import Error as SSLError
        else:
            class SSLError(Exception): pass
        try:
            self.server = server_class((interface, port), handler_class, 0)
        except SSLError, e:
            Logger().notifyChannel('xml-rpc-ssl', LOG_CRITICAL, "Can not load the certificate and/or the private key files")
            sys.exit(1)
        except Exception, e:
            Logger().notifyChannel('xml-rpc', LOG_CRITICAL, "Error occur when starting the server daemon: %s" % (e,))
            sys.exit(1)


    def attach(self, path, gw):
        pass

    def stop(self):
        self.running = False
        _close_socket(self.server.socket)

    def run(self):
        self.server.register_introspection_functions()

        self.running = True
        while self.running:
            try:
                self.server.handle_request()
            except (socket.error, select.error), e:
                if self.running or e.args[0] != errno.EBADF:
                    raise
        return True

        # If the server need to be run recursively
        #
        #signal.signal(signal.SIGALRM, self.my_handler)
        #signal.alarm(6)
        #while True:
        #   self.server.handle_request()
        #signal.alarm(0)          # Disable the alarm

import tiny_socket
class TinySocketClientThread(threading.Thread, OpenERPDispatcher):
    def __init__(self, sock, threads):
        threading.Thread.__init__(self)
        self.sock = sock
        self.threads = threads

    def run(self):
        self.running = True
        try:
            ts = tiny_socket.mysocket(self.sock)
        except:
            self.sock.close()
            self.threads.remove(self)
            return False
        while self.running:
            try:
                msg = ts.myreceive()
            except:
                self.sock.close()
                self.threads.remove(self)
                return False
            try:
                result = self.dispatch(msg[0], msg[1], msg[2:])
                ts.mysend(result)
            except OpenERPDispatcherException, e:
                new_e = Exception(tools.exception_to_unicode(e.exception)) # avoid problems of pickeling
                try:
                    ts.mysend(new_e, exception=True, traceback=e.traceback)
                except:
                    self.sock.close()
                    self.threads.remove(self)
                    return False

            self.sock.close()
            self.threads.remove(self)
            return True

    def stop(self):
        self.running = False


class TinySocketServerThread(threading.Thread):
    def __init__(self, interface, port, secure=False):
        threading.Thread.__init__(self)
        self.__port = port
        self.__interface = interface
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.__interface, self.__port))
        self.socket.listen(5)
        self.threads = []

    def run(self):
        try:
            self.running = True
            while self.running:
                timeout = self.socket.gettimeout()
                fd_sets = select.select([self.socket], [], [], timeout)
                if not fd_sets[0]:
                    continue
                (clientsocket, address) = self.socket.accept()
                ct = TinySocketClientThread(clientsocket, self.threads)
                self.threads.append(ct)
                ct.start()
            self.socket.close()
        except Exception, e:
            self.socket.close()
            return False

    def stop(self):
        self.running = False
        for t in self.threads:
            t.stop()
        _close_socket(self.socket)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
