#!/usr/bin/env python

# Copyright 2015 Jason Edelman <jedelman8@gmail.com>
# Network to Code, LLC
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
    import collections
    from pycsco.nxos.error import CLIError
    from pycsco.nxos.utils import legacy
except ImportError as e:
    print '*' * 30
    print e
    print '*' * 30

__all__ = []


def get_acl(device, acl_name, seq_number):
    """Retrieves ACL configuration

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class from pycsco
        acl_name (str): Case-sensitive name of the ACL
        seq_number (str): Number of sequence number you are looking for

    Returns:
        Dictionary, List, List
          Dictionary: of the entry mapped to the seq number
          List: all ACEs in the ACL
          List: all sequence numbers in the ACL
    """
    command = 'show ip access-list ' + acl_name

    new_acl = []
    saveme = {}
    seqs = []

    try:
        data = device.show(command)
    except CLIError:
        return saveme, new_acl, seqs

    data_dict = xmltodict.parse(data[1])

    code = data_dict['ins_api']['outputs']['output']['code']

    if code == '501':  # acl doesn't exist, but CLI doesn't return an error
        return saveme, new_acl, seqs

    try:
        acl_body = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_ip_ipv6_mac')['ROW_ip_ipv6_mac']
        acl_entries = acl_body['TABLE_seqno']['ROW_seqno']
        acl_name = acl_body.get('acl_name')

    except KeyError:  # could be raised if no ACEs are configured for an ACL
        return saveme, {'acl': 'no_entries'}, seqs

    try:
        for each in acl_entries:
            temp = collections.OrderedDict()
            keep = {}
            temp['name'] = acl_name
            temp['seq'] = each.get('seqno')
            temp['options'] = {}
            remark = each.get('remark')
            if remark:
                temp['remark'] = remark
                temp['action'] = 'remark'
            else:
                temp['action'] = each.get('permitdeny')
                temp['proto'] = each.get('proto', each.get('proto_str', each.get('ip')))
                temp['src'] = each.get('src_any', each.get('src_ip_prefix'))
                temp['src_port_op'] = each.get('src_port_op')
                temp['src_port1'] = each.get('src_port1_num')
                temp['src_port2'] = each.get('src_port2_num')
                temp['dest'] = each.get('dest_any', each.get('dest_ip_prefix'))
                temp['dest_port_op'] = each.get('dest_port_op')
                temp['dest_port1'] = each.get('dest_port1_num')
                temp['dest_port2'] = each.get('dest_port2_num')

                options = collections.OrderedDict()
                options['log'] = each.get('log')
                options['urg'] = each.get('urg')
                options['ack'] = each.get('ack')
                options['psh'] = each.get('psh')
                options['rst'] = each.get('rst')
                options['syn'] = each.get('syn')
                options['fin'] = each.get('fin')
                options['established'] = each.get('established')
                options['dscp'] = each.get('dscp_str')
                options['precedence'] = each.get('precedence_str')
                options['fragments'] = each.get('fragments')
                options['time_range'] = each.get('timerange')

                options_no_null = {}
                for k, v in options.iteritems():
                    if v is not None:
                        options_no_null[k] = v

                keep['options'] = options_no_null

            for k, v in temp.iteritems():
                if v:
                    keep[k] = v

            # ensure options is always in the dict
            if keep.get('options', 'DNE') == 'DNE':
                keep['options'] = {}

            if keep.get('seq') == seq_number:
                saveme = dict(keep)

            seqs.append(str(keep.get('seq')))
            new_acl.append(keep)
    except AttributeError:
        temp = collections.OrderedDict()
        keep = {}
        each = acl_entries
        temp['name'] = acl_name
        temp['seq'] = each.get('seqno')
        temp['options'] = {}
        remark = each.get('remark')
        if remark:
            temp['remark'] = remark
            temp['action'] = 'remark'
        else:
            temp['action'] = each.get('permitdeny')
            temp['proto'] = each.get('proto', each.get('proto_str'))
            temp['src'] = each.get('src_any', each.get('src_ip_prefix'))
            temp['src_port_op'] = each.get('src_port_op')

            temp['src_port1'] = each.get('src_port1_num')
            temp['src_port2'] = each.get('src_port2_num')
            temp['dest'] = each.get('dest_any', each.get('dest_ip_prefix'))
            temp['dest_port_op'] = each.get('dest_port_op')
            temp['dest_port1'] = each.get('dest_port1_num')
            temp['dest_port2'] = each.get('dest_port2_num')

            options = collections.OrderedDict()
            options['log'] = each.get('log')
            options['urg'] = each.get('urg')
            options['ack'] = each.get('ack')
            options['psh'] = each.get('psh')
            options['rst'] = each.get('rst')
            options['syn'] = each.get('syn')
            options['fin'] = each.get('fin')
            options['established'] = each.get('established')
            options['dscp'] = each.get('dscp_str')
            options['precedence'] = each.get('precedence_str')
            options['fragments'] = each.get('fragments')
            options['time_range'] = each.get('timerange')

            options_no_null = {}
            for k, v in options.iteritems():
                if v:
                    options_no_null[k] = v

            keep['options'] = options_no_null

        for k, v in temp.iteritems():
            if v:
                keep[k] = v

        # ensure options is always in the dict
        if not keep.get('options'):
            keep['options'] = {}

        if keep.get('seq') == seq_number:
            saveme = keep

        seqs.append(str(keep.get('seq')))
        new_acl.append(keep)

    except:
        return {'value': 'error'}, [], []

    return saveme, new_acl, seqs


def _acl_operand(operand, srcp1, sprcp2):

    sub_entry = ' ' + operand

    if operand == 'range':
        sub_entry += ' ' + srcp1 + ' ' + sprcp2
    else:
        sub_entry += ' ' + srcp1

    return sub_entry


def config_core_acl(proposed):
    """Generate command string to configure an ACE

    Args:
        proposed (dict): k/v pairs sent in from Ansible

    Returns:
        String
    """

    seq = proposed.get('seq')
    action = proposed.get('action')
    remark = proposed.get('remark')
    proto = proposed.get('proto')
    src = proposed.get('src')
    src_port_op = proposed.get('src_port_op')
    src_port1 = proposed.get('src_port1')
    src_port2 = proposed.get('src_port2')

    dest = proposed.get('dest')
    dest_port_op = proposed.get('dest_port_op')
    dest_port1 = proposed.get('dest_port1')
    dest_port2 = proposed.get('dest_port2')

    ace_start_entries = [action, proto, src]
    if not remark:
        ace = seq + ' ' + ' '.join(ace_start_entries)
        if src_port_op:
            ace += _acl_operand(src_port_op, src_port1, src_port2)
        ace += ' ' + dest
        if dest_port_op:
            ace += _acl_operand(dest_port_op, dest_port1, dest_port2)
    else:
        ace = seq + ' remark ' + remark

    return ace


def config_acl_options(options):
    """If options required, this is used to generate the required command
       string

    Args:
        options (dict): key/value pairs from Ansible
    Returns:
        String or nothing
    """

    ENABLE_ONLY = ['psh', 'urg', 'log', 'ack', 'syn',
                   'established', 'rst', 'fin', 'fragments',
                   'log']

    OTHER = ['dscp', 'precedence', 'time-range']
    # packet-length is the only option not currently supported

    if options.get('time_range'):
        options['time-range'] = options.get('time_range')
        options.pop('time_range')

    command = ''
    for option, value in options.iteritems():
        if option in ENABLE_ONLY:
            if value == 'enable':
                command += ' ' + option
        elif option in OTHER:
            command += ' ' + option + ' ' + value
    if command:
        command = command.strip()
        return command


def get_acl_interface(device, acl):
    """Checks to see if an ACL is applied to an interface

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class
        acl (str): Name of the ACL

    Returns:
        Dictionary- keys: applied, direction
    """
    command = 'show ip access-list summary'
    data = device.show(command, text=True)
    data_dict = xmltodict.parse(data[1])

    raw_text = data_dict['ins_api']['outputs']['output']['body']

    existing = legacy.get_structured_data('acl_interface.tmpl', raw_text)

    existing_no_null = []
    temp = {}
    for each in existing:
        if each.get('name') == acl:
            temp['interface'] = each.get('interface').lower()
            each.update(temp)
            existing_no_null.append(each)

    return existing_no_null


def other_existing_acl(get_existing, interface, direction):
    """Gets entries of this ACL on the interface

    Args:
        get_existing (list): list from get_acl_interface
        interface (str): **FULL** name of interface
        direction: (str): egress | ingress

    Returns:
        List: each entry if another element (in/out)
        Dictionary: the entry if it exists, else {}
    """

    # now we'll just get the interface in question
    # needs to be a list since same acl could be applied in both dirs
    acls_interface = []
    if get_existing:
        for each in get_existing:
            if each.get('interface') == interface:
                acls_interface.append(each)
    else:
        acls_interface = []

    if acls_interface:
        this = {}
        for each in acls_interface:
            if each.get('direction') == direction:
                this = each
    else:
        acls_interface = []
        this = {}

    return acls_interface, this


def apply_acl(proposed):
    """Generate list of commands to apply ACL

    Args:
        proposed (dict): K/V pairs with data about the ACL to apply

    Returns:
        List
    """
    commands = []

    commands.append('interface ' + proposed.get('interface'))
    direction = proposed.get('direction')
    if direction == 'egress':
        cmd = 'ip access-group {0} {1}'.format(proposed.get('name'), 'out')
    elif direction == 'ingress':
        cmd = 'ip access-group {0} {1}'.format(proposed.get('name'), 'in')
    commands.append(cmd)

    return commands


def remove_acl(proposed):
    """Generate list of commands to remove ACL

    Args:
        proposed (dict): K/V pairs with data about the ACL to apply

    Returns:
        List
    """
    commands = []

    commands.append('interface ' + proposed.get('interface'))
    direction = proposed.get('direction')
    if direction == 'egress':
        cmd = 'no ip access-group {0} {1}'.format(proposed.get('name'), 'out')
    elif direction == 'ingress':
        cmd = 'no ip access-group {0} {1}'.format(proposed.get('name'), 'in')
    commands.append(cmd)

    return commands


if __name__ == "__main__":
    import json
    from pycsco.nxos.device import Device
    device = Device(ip='n9396-2', username='cisco', password='!cisco123!',
                    protocol='http')

    seq_number = '40'

    data = get_acl_interface(device, 'MYACL')
    print json.dumps(data, indent=4)
    # print json.dumps(ace, indent=4)

    '''
    core = config_core_acl(ace, {})

    if ace.get('options'):
        print core + ' ' + config_acl_options(ace.get('options'))
    else:
        print core
    '''
