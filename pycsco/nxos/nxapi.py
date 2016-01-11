#!/usr/bin/env python
# Copyright (C) 2013 Cisco Systems Inc.
# All rights reserved
try:
    import urllib2
    import contextlib
    import base64
    import socket
    import httplib
    from httplib import HTTPConnection, HTTPS_PORT
    import ssl
except ImportError as e:
    print '***************************'
    print e
    print '***************************'


class HTTPSConnection(HTTPConnection):

    '''This class allows communication via SSL.'''

    default_port = HTTPS_PORT

    def __init__(
        self,
        host,
        port=None,
        key_file=None,
        cert_file=None,
        strict=None,
        timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
        source_address=None
    ):

        HTTPConnection.__init__(
            self,
            host,
            port,
            strict,
            timeout,
            source_address,
            )
        self.key_file = key_file
        self.cert_file = cert_file

    def connect(self):
        '''Connect to a host on a given (SSL) port.'''

        sock = socket.create_connection((self.host, self.port),
                                        self.timeout, self.source_address)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()

        # this is the only line we modified from the httplib.py file
        # we added the ssl_version variable
        self.sock = ssl.wrap_socket(sock, self.key_file,
                                    self.cert_file,
                                    ssl_version=ssl.PROTOCOL_SSLv3)

# Many changes to httplib were made around Python 2.6/2.7 and this monkey
# patch breaks the code. I have not been able to figure out why the
# originators of this code felt it necessary to add the ssl_version variable,
# but everything seems to be working fine without it. The variable is not
# referenced anywhere in the entire pycsco code tree. To avoid further
# problems in the future the monkey patch has been disabled by commenting the
# line below. The entire HTTPSConnection class should be removed sometime in
# the future. // jonas@stenling.se
#
#httplib.HTTPSConnection = HTTPSConnection


class RequestMsg:

    def __init__(
        self,
        msg_type='cli_show',
        ver='0.1',
        sid='1',
        input_cmd='show version',
        out_format='json',
        do_chunk='0',
    ):

        self.msg_type = msg_type
        self.ver = ver
        self.sid = sid
        self.input_cmd = input_cmd
        self.out_format = out_format
        self.do_chunk = do_chunk

    def get_req_msg_str(
        self,
        msg_type='cli_show',
        ver='0.1',
        sid='1',
        input_cmd='show version',
        out_format='json',
        do_chunk='0',
    ):

        req_msg = '<?xml version="1.0" encoding="ISO-8859-1"?>\n'
        req_msg += '<ins_api>\n'
        req_msg += '<type>' + msg_type + '</type>\n'
        req_msg += '<version>' + ver + '</version>\n'
        req_msg += '<chunk>' + do_chunk + '</chunk>\n'
        req_msg += '<sid>' + sid + '</sid>\n'
        req_msg += '<input>' + input_cmd + '</input>\n'
        req_msg += '<output_format>' + out_format + '</output_format>\n'
        req_msg += '</ins_api>\n'
        return req_msg


class RespFetcher:

    def __init__(
        self,
        username='admin',
        password='insieme',
        url='http://172.21.128.227/ins',
    ):

        self.username = username
        self.password = password
        self.url = url
        self.base64_str = base64.encodestring('%s:%s' % (username,
                                              password)).replace('\n', '')

    def get_resp(
        self,
        req_str,
        cookie,
        timeout,
    ):

        req = urllib2.Request(self.url, req_str)
        req.add_header('Authorization', 'Basic %s' % self.base64_str)
        req.add_header('Cookie', '%s' % cookie)
        try:
            with contextlib.closing(urllib2.urlopen(req,
                                    timeout=timeout)) as resp:
                resp_str = resp.read()
                resp_headers = resp.info()
                return (resp_headers, resp_str)
        except socket.timeout, e:
            print 'Req timeout'
            raise


class RespFetcherHttps:

    def __init__(
        self,
        username='admin',
        password='insieme',
        url='https://172.21.128.227/ins',
    ):

        self.username = username
        self.password = password
        self.url = url
        self.base64_str = base64.encodestring('%s:%s' % (username,
                                              password)).replace('\n', '')

    def get_resp(
        self,
        req_str,
        cookie,
        timeout,
    ):

        req = urllib2.Request(self.url, req_str)
        req.add_header('Authorization', 'Basic %s' % self.base64_str)
        req.add_header('Cookie', '%s' % cookie)
        try:
            with contextlib.closing(urllib2.urlopen(req,
                                    timeout=timeout)) as resp:
                resp_str = resp.read()
                resp_headers = resp.info()
                return (resp_headers, resp_str)
        except socket.timeout, e:
            print 'Req timeout'
            raise


class NXAPI:
    '''A better NX-API utility'''
    def __init__(self):
        self.target_url = 'http://localhost/ins'
        self.username = 'admin'
        self.password = 'admin'
        self.timeout = 30

        self.ver = '0.1'
        self.msg_type = 'cli_show'
        self.cmd = 'show version'
        self.out_format = 'xml'
        self.do_chunk = '0'
        self.sid = 'sid'
        self.cookie = 'no-cookie'

    def set_target_url(self, target_url='http://localhost/ins'):
        self.target_url = target_url

    def set_username(self, username='admin'):
        self.username = username

    def set_password(self, password='admin'):
        self.password = password

    def set_timeout(self, timeout=0):
        if timeout < 0:
            raise data_type_error('timeout should be greater than 0')
        self.timeout = timeout

    def set_cmd(self, cmd=''):
        self.cmd = cmd

    def set_out_format(self, out_format='xml'):
        if out_format != 'xml' and out_format != 'json':
            raise data_type_error('out_format xml or json')
        self.out_format = out_format

    def set_do_chunk(self, do_chunk='0'):
        if do_chunk != 0 and do_chunk != 1:
            raise data_type_error('do_chunk 0 or 1')
        self.do_chunk = do_chunk

    def set_sid(self, sid='sid'):
        self.sid = sid

    def set_cookie(self, cookie='no-cookie'):
        self.cookie = cookie

    def set_ver(self, ver='0.1'):
        if ver != '0.1':
            raise data_type_error('Only ver 0.1 supported')
        self.ver = ver

    def set_msg_type(self, msg_type='cli_show'):
        if msg_type != 'cli_show' and msg_type != 'cli_show_ascii' \
            and msg_type != 'cli_conf' and msg_type != 'bash':
            raise data_type_error('msg_type incorrect')
        self.msg_type = msg_type

    def get_target_url(self):
        return self.target_url

    def get_username(self):
        return self.username

    def get_password(self):
        return self.username

    def get_timeout(self):
        return self.timeout

    def get_cmd(self):
        return self.cmd

    def get_out_format(self):
        return self.out_format

    def get_do_chunk(self):
        return self.do_chunk

    def get_sid(self):
        return self.sid

    def get_cookie(self):
        return self.cookie

    def req_to_string(self):
        req_msg = '<?xml version="1.0" encoding="ISO-8859-1"?>\n'
        req_msg += '<ins_api>\n'
        req_msg += '<type>' + self.msg_type + '</type>\n'
        req_msg += '<version>' + self.ver + '</version>\n'
        req_msg += '<chunk>' + self.do_chunk + '</chunk>\n'
        req_msg += '<sid>' + self.sid + '</sid>\n'
        req_msg += '<input>' + self.cmd + '</input>\n'
        req_msg += '<output_format>' + self.out_format + '</output_format>\n'
        req_msg += '</ins_api>\n'
        return req_msg

    def send_req(self):
        req = RespFetcher(self.username, self.password, self.target_url)
        return req.get_resp(self.req_to_string(), self.cookie, self.timeout)
