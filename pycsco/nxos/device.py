#!/usr/bin/env python

# Copyright 2015 Jason Edelman <jedelman8@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

try:
    import xmltodict
    import os.path
    import yaml
    from os.path import expanduser
    from nxapi import NXAPI
except ImportError as e:
    print '***************************'
    print e
    print '***************************'


class Auth():
    def __init__(self, vendor, model):
        home = expanduser('~')
        self.username = None
        self.password = None
        creds_file = home + '/.netauth'
        if os.path.isfile(creds_file):
            with open(creds_file, 'r') as creds:
                auth = yaml.load(creds)
            try:
                self.username = auth[vendor][model]['username']
                self.password = auth[vendor][model]['password']
            except:
                pass


class Device():

    def __init__(self,
                 username='cisco',
                 password='cisco',
                 ip='192.168.200.50',
                 protocol='http'):

        if protocol not in ('http', 'https'):
            raise ValueError('protocol must be http or https')

        self.username = username
        self.password = password
        self.ip = ip
        self.protocol = protocol
        self.sw1 = NXAPI()
        self.sw1.set_target_url('%s://%s/ins' % (self.protocol, self.ip))
        self.sw1.set_username(self.username)
        self.sw1.set_password(self.password)

    def open(self):
        # keeping to phase out programs that still use it.
        pass

    def show(self, command, fmat='xml', text=False):

        if text is False:
            self.sw1.set_msg_type('cli_show')
        elif text:
            self.sw1.set_msg_type('cli_show_ascii')

        self.sw1.set_out_format(fmat)
        self.sw1.set_cmd(command)

        return self.sw1.send_req()

    def config(self, command, fmat='xml'):

        self.sw1.set_msg_type('cli_conf')
        self.sw1.set_out_format(fmat)
        self.sw1.set_cmd(command)

        # return self.sw1.send_req
        data = self.sw1.send_req()
        clierror = None
        data_dict = xmltodict.parse(data[1])

        error_check_list = data_dict['ins_api']['outputs']['output']
        try:
            for each in error_check_list:
                clierror = each.get('clierror', None)
                msg = each.get('msg', None)
        except AttributeError:
            clierror = error_check_list.get('clierror', None)
            msg = error_check_list.get('msg', None)
        except:
            return data

        if clierror:
            raise IOError(clierror, msg)
        return data
