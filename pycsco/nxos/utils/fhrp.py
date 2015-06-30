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

"""This module contains a number of functions.  There are zero classes
at this time.  It should be noted that these functions were built for the sole
purpose of supporting Ansible modules (github.com/jedelman8/nxos-ansible).
While that is the case, many of them can also be used independently of
Ansible.  You can simply do a 'from pycsco.nxos.utils.nxapi_lib import *'
to see which functions can be used independent of Ansible.  Overtime, the goal
is to make this more object oriented, efficient, and optimal for support
Ansible modules and in addition, general development.

"""
try:
    import xmltodict
    from pycsco.nxos.device import Device
except ImportError as e:
    print '*' * 30
    print e
    print '*' * 30

__all__ = []


def get_vrrp_existing(device, interface):
    """Gets vrrp groups configured on each interface

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py

    Returns:
        dict: k/v pairs in the form of interface/[group list]

    """
    command = 'show vrrp detail interface ' + interface
    xmlReturnData = device.show(command)
    result = xmltodict.parse(xmlReturnData[1])
    vrrp = []
    try:
        get_data = result['ins_api']['outputs']['output']['body'].get(
            'TABLE_vrrp_group')
        # ['ROW_vrrp_group']

        # print type(get_data[0])
        # print get_data[0]['ROW_vrrp_group']
        try:
            for entry in get_data:
                get_dict = entry['ROW_vrrp_group']
                group = get_dict.get('sh_group_id')
                vip = get_dict.get('sh_vip_addr')
                priority = get_dict.get('sh_priority')
                preempt = get_dict.get('sh_group_preempt')
                auth = get_dict.get('sh_auth_text')
                interval = get_dict.get('sh_adv_interval')

                if preempt == 'Disable':
                    preempt = False
                elif preempt == 'Enable':
                    preempt = True

                temp = dict(group=group, vip=vip, priority=priority,
                            preempt=preempt, auth=auth, interval=interval)
                vrrp.append(temp)

        except TypeError:
            get_dict = get_data['ROW_vrrp_group']

            group = get_dict.get('sh_group_id')
            vip = get_dict.get('sh_vip_addr')
            priority = get_dict.get('sh_priority')
            preempt = get_dict.get('sh_group_preempt')
            auth = get_dict.get('sh_auth_text')
            interval = get_dict.get('sh_adv_interval')
            if preempt == 'Disable':
                preempt = False
            elif preempt == 'Enable':
                preempt = True
            temp = dict(group=group, vip=vip, priority=priority,
                        preempt=preempt, auth=auth, interval=interval)
            vrrp.append(temp)

    except (KeyError, AttributeError):
        vrrp = []

    return vrrp


def get_commands_config_vrrp(delta):
    """Gets commands to config vrrp on an interface

    Args:
        delta (dict): vrrp params to config

    Returns:
        list: ordered list of commands to config vrrp

    """

    commands = []

    CMDS = {
        'priority': 'priority {0}',
        'preempt': 'preempt',
        'vip': 'address {0}',
        'interval': 'advertisement-interval {0}',
        'auth': 'authentication text {0}'
    }

    vip = delta.get('vip')
    prio = delta.get('priority')
    preempt = delta.get('preempt')
    interval = delta.get('interval')
    auth = delta.get('auth')

    if vip:
        commands.append((CMDS.get('vip')).format(vip))
    if prio:
        commands.append((CMDS.get('priority')).format(prio))
    if preempt:
        commands.append(CMDS.get('preempt'))
    elif preempt is False:
        commands.append('no ' + CMDS.get('preempt'))
    if interval:
        commands.append((CMDS.get('interval')).format(interval))
    if auth:
        commands.append((CMDS.get('auth')).format(auth))

    return commands


def get_existing_vrrp(device, interface, group):

    existing_groups = get_vrrp_existing(device, interface)
    existing = {}
    if existing_groups:
        for specific_group in existing_groups:
            if specific_group.get('group') == group:
                existing = specific_group

    return existing


def get_commands_remove_vrrp(group):
    """Gets commands to remove an hsrp on an interface

    Args:
        group (str): hsrp group

    Returns:
        list: ordered list of commands to remove the hsrp group

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    commands = []
    commands.append('no vrrp ' + group)
    return commands


if __name__ == "__main__":

    device = Device(ip='n9396-2', username='cisco',
                    password='!cisco123!', protocol='http')

    interface = 'vlan100'
    test = get_vrrp_existing(device, interface)

    import json
    print json.dumps(test, indent=4)
