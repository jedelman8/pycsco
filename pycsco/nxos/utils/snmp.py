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

from pycsco.nxos.device import Device
from pycsco.nxos.utils import legacy

import json

try:
    import xmltodict
except ImportError as e:
    print '*' * 30
    print e
    print '*' * 30

__all__ = []


def get_snmp_community(device, find_filter=None):
    """Retrieves snmp community settings for a given device

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class
        community (str): optional arg to filter out this specific community

    Returns:
        dictionary
    """
    command = 'show snmp community'
    data = device.show(command)
    data_dict = xmltodict.parse(data[1])

    c_dict = {}

    try:
        comm_table = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_snmp_community')['ROW_snmp_community']

        for each in comm_table:
            community = {}
            key = str(each['community_name'])
            community['group'] = str(each['grouporaccess'])
            community['acl'] = str(each['aclfilter'])
            c_dict[key] = community

    except (TypeError):
            community = {}
            key = str(each['community_name'])
            community['group'] = str(comm_table['grouporaccess'])
            community['acl'] = str(comm_table['aclfilter'])
            c_dict[key] = community

    except (KeyError, AttributeError):
        return c_dict

    if find_filter:
        find = c_dict.get(find_filter, None)

    if find_filter is None or find is None:
        return {}
    else:
        return find


def remove_snmp_community(community):
    return ['no snmp-server community ' + community]


def config_snmp_community(delta, community):
    CMDS = {
        'group': 'snmp-server community {0} group {group}',
        'acl': 'snmp-server community {0} use-acl {acl}'
    }
    commands = []
    for k, v in delta.iteritems():
        cmd = CMDS.get(k).format(community, **delta)
        if cmd:
            commands.append(cmd)
            cmd = None
    return commands


def get_snmp_groups(device):
    """Retrieves snmp groups for a given device

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class

    Returns:
        list of groups
    """
    command = 'show snmp group'
    data = device.show(command)
    data_dict = xmltodict.parse(data[1])

    g_list = []

    try:
        group_table = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_role')['ROW_role']
        for each in group_table:
            g_list.append(each['role_name'])

    except (KeyError, AttributeError):
        return g_list

    return g_list


def remove_snmp_user(user):
    return ['no snmp-server user ' + user]


def config_snmp_user(proposed, user, reset, new):
    # check to see if it was a new config
    # and see if it is going from a non-encrypted
    # password to an encrypted one
    if reset and not new:
        commands = remove_snmp_user(user)
    else:
        commands = []

    group = proposed.get('group', None)

    cmd = ''

    if group:
        cmd = 'snmp-server user {0} {group}'.format(user, **proposed)

    auth = proposed.get('authentication', None)
    pwd = proposed.get('pwd', None)

    if auth and pwd:
        cmd += ' auth {authentication} {pwd}'.format(**proposed)

    encrypt = proposed.get('encrypt', None)
    privacy = proposed.get('privacy', None)

    if encrypt and privacy:
        cmd += ' priv {encrypt} {privacy}'.format(**proposed)
    elif privacy:
        cmd += ' priv {privacy}'.format(**proposed)

    if cmd:
        commands.append(cmd)

    return commands


def get_snmp_user(device, user):
    """Retrieves snmp user configuration for a given user on a given device

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class
        user (str): name of user (max size 28 chars)

    Returns:
        dictionary
    """
    command = 'show snmp user ' + user
    data = device.show(command)
    data_dict = xmltodict.parse(data[1])

    resource = {}

    try:
        resource_table = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_snmp_users')['ROW_snmp_users']

        resource['user'] = str(resource_table['user'])
        resource['authentication'] = str(resource_table['auth']).strip()
        encrypt = str(resource_table['priv']).strip()
        if encrypt.startswith('aes'):
            resource['encrypt'] = 'aes-128'
        else:
            resource['encrypt'] = 'none'

        group_table = resource_table['TABLE_groups']['ROW_groups']

        groups = []
        try:
            for group in group_table:
                groups.append(str(group['group']))
        except TypeError:
            groups.append(str(group_table['group']))

        resource['group'] = groups

    except (KeyError, AttributeError):
        return resource

    return resource


def get_snmp_contact(device):
    """Retrieves snmp contact from a device

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class

    Returns:
        dictionary
    """
    command = 'show run snmp'
    data = device.show(command, text=True)
    data_dict = xmltodict.parse(data[1])

    raw_text = data_dict['ins_api']['outputs']['output']['body']

    existing = legacy.get_structured_data('snmp_contact.tmpl', raw_text)

    if len(existing) == 1:
        return existing[0]

    return existing


def get_snmp_location(device):
    """Retrieves snmp location from a device

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class

    Returns:
        dictionary
    """
    command = 'show run snmp'
    data = device.show(command, text=True)
    data_dict = xmltodict.parse(data[1])

    raw_text = data_dict['ins_api']['outputs']['output']['body']

    existing = legacy.get_structured_data('snmp_location.tmpl', raw_text)

    if len(existing) == 1:
        return existing[0]

    return existing


def get_snmp_host(device, host):
    """Retrieves snmp host configuration for a given host on a given device

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class
        host (str): IP Address or hostname of snmp host

    Returns:
        dictionary
    """
    command = 'show snmp host'
    data = device.show(command)
    data_dict = xmltodict.parse(data[1])

    resource = {}

    try:
        resource_table = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_host')['ROW_host']

        for each in resource_table:
            temp = {}
            key = str(each['host'])
            temp['udp'] = str(each['port']).strip()
            temp['version'] = str(each['version']).strip()
            temp['v3'] = str(each['level']).strip()
            temp['type'] = str(each['type']).strip()
            temp['community'] = str(each['secname']).strip()
            src = each.get('src_intf', None)
            if src:
                temp['src_intf'] = src.split(':')[1].strip()

            vrf_filt = each.get('TABLE_vrf_filters', None)
            if vrf_filt:
                temp['vrf_filter'] = vrf_filt['ROW_vrf_filters']['vrf_filter'].split(':')[1].split(',')

            vrf = each.get('vrf', None)
            if vrf:
                temp['vrf'] = vrf.split(':')[1].strip()

            resource[key] = temp

    except (TypeError):
        temp = {}
        key = str(resource_table['host'])
        temp['udp'] = str(resource_table['port']).strip()
        temp['version'] = str(resource_table['version']).strip()
        temp['v3'] = str(resource_table['level']).strip()
        temp['type'] = str(resource_table['type']).strip()
        temp['community'] = str(resource_table['secname']).strip()
        src = resource_table.get('src_intf', None)
        if src:
            temp['src_intf'] = src.split(':')[1].strip()

        vrf_filt = resource_table.get('TABLE_vrf_filters', None)
        if vrf_filt:
            temp['vrf_filter'] = vrf_filt['ROW_vrf_filters']['vrf_filter'].split(':')[1].split(',')

        vrf = resource_table.get('vrf', None)
        if vrf:
            temp['vrf'] = vrf.split(':')[1].strip()

        resource[key] = temp

    except (KeyError, AttributeError):
        return resource

    find = resource.get(host, None)
    if find:
        return find
    else:
        return {}


def remove_snmp_host(host, existing):

    commands = []
    if existing['version'] == 'v3':
        existing['version'] = '3'
        command = 'no snmp-server host {0} {type} version {version} {v3} {community}'.format(host, **existing)
    elif existing['version'] == 'v2c':
        existing['version'] = '2c'
        command = 'no snmp-server host {0} {type} version {version} {community}'.format(host, **existing)

    if command:
        commands.append(command)
    return commands


def config_snmp_host(delta, proposed, existing):

    commands = []

    host = proposed['snmp_host']

    cmd = 'snmp-server host ' + proposed['snmp_host']

    type1 = delta.get('type', None)
    version = delta.get('version', None)
    ver = delta.get('v3', None)
    community = delta.get('community', None)

    if any([type1, version, ver, community]):
        cmd += ' ' + (type1 or existing.get('type'))

        version = version or existing.get('version')
        if version == 'v2c':
            vn = '2c'
        elif version == 'v3':
            vn = '3'

        cmd += ' version ' + vn

        if ver:
            cmd += ' '
            cmd += (ver or existing.get('v3'))

        cmd += ' '
        cmd += (community or existing.get('community'))

        commands.append(cmd)

    CMDS = {
        'vrf_filter': 'snmp-server host {0} filter-vrf {vrf_filter}',
        'vrf': 'snmp-server host {0} use-vrf {vrf}',
        'udp': 'snmp-server host {0} udp-port {udp}',
        'src_intf': 'snmp-server host {0} source-interface {src_intf}'
    }

    for key, value in delta.iteritems():
        if key in ['vrf_filter', 'vrf', 'udp', 'src_intf']:
            command = CMDS.get(key, None)
            if command:
                cmd = command.format(host, **delta)
                commands.append(cmd)
            cmd = None

    return commands


def get_snmp_traps(device, group):
    """Retrieves snmp traps configuration for a given device

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class
        group (str): group of snmp traps as defined in the switch

    Returns:
        list
    """
    command = 'show snmp trap'
    data = device.show(command)
    data_dict = xmltodict.parse(data[1])

    resource = {}

    try:
        resource_table = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_snmp_trap')['ROW_snmp_trap']

        for each in ['aaa', 'bridge', 'callhome', 'cfs', 'config', 'entity',
                     'feature-control', 'hsrp', 'license', 'link', 'lldp',
                     'ospf', 'rf', 'rmon', 'snmp', 'storm-control', 'stpx',
                     'sysmgr', 'system', 'upgrade', 'vtp']:

            resource[each] = []

        for each in resource_table:
            temp = {}

            key = str(each['trap_type'])

            temp['trap'] = str(each['description'])
            temp['enabled'] = str(each['isEnabled'])

            if key != 'Generic':
                resource[key].append(temp)

    except (KeyError, AttributeError):
        return resource

    find = resource.get(group, None)

    if group == 'all'.lower():
        return resource
    elif find:
        return find
    else:
        return []
