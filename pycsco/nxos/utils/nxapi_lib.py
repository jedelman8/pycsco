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
    import re
    from pycsco.nxos.error import CLIError
except ImportError as e:
    print '*' * 30
    print e
    print '*' * 30

__all__ = ['cmd_list_to_string', 'create_dir', 'feature_enabled',
           'get_active_vpc_peer_link', 'get_interface_running_config',
           'get_existing_portchannel_to_vpc_mappings', 'get_facts', 'get_vrf',
           'get_feature_list', 'get_hsrp_group', 'get_interface_mode',
           'get_hsrp_groups_on_interfaces', 'vlan_range_to_list',
           'switch_files_list', 'get_interface', 'get_interface_detail',
           'get_interface_type', 'get_interfaces_dict', 'get_ipv4_interface',
           'get_list_of_vlans', 'get_vlan_info', 'get_min_links', 'get_mtu',
           'get_neighbors', 'get_portchannel', 'get_portchannel_list',
           'get_portchannel_vpc_config', 'get_switchport', 'get_system_mtu',
           'get_udld_global', 'get_udld_interface', 'get_vlan', 'get_vpc',
           'get_vpc_running_config', 'get_vrf_list', 'peer_link_exists',
           'interface_is_portchannel', 'is_default', 'is_interface_copper',
           'delete_dir','interface_range_to_list']


def get_vlan(device, vid):
    """Retrieves attributes of a given VLAN based on a VLAN ID

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        vid (str): The VLAN ID of which you want details for

    Returns:
        dictionary:
            if VLAN exists - k/v pairs include vlan_id, name,
                vlan_state
            else: returns empty dictionary

    """
    command = 'show vlan id ' + vid
    try:
        data = device.show(command)
    except CLIError:
        return {}
    data_dict = xmltodict.parse(data[1])
    vlan = {}

    try:
        vdata = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_vlanbriefid')['ROW_vlanbriefid']
        vlan['vlan_id'] = str(vdata['vlanshowbr-vlanid-utf'])
        vlan['name'] = str(vdata['vlanshowbr-vlanname'])
        vlan['vlan_state'] = str(vdata['vlanshowbr-vlanstate'])
        state = str(vdata['vlanshowbr-shutstate'])

        if state == 'shutdown':
            vlan['admin_state'] = 'down'
        elif state == 'noshutdown':
            vlan['admin_state'] = 'up'
    except (KeyError, AttributeError):
        return vlan

    return vlan


def get_list_of_vlans(device):
    """Used to retrieve a list of all VLANs on a device.

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py

    Returns:
        list of all VLANs on the switch

    """
    command = 'show vlan'
    data = device.show(command)
    data_dict = xmltodict.parse(data[1])
    vlans = []

    try:
        vlan_list = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_vlanbrief')['ROW_vlanbrief']
        for vlanid in vlan_list:
            vlans.append(str(vlanid['vlanshowbr-vlanid-utf']))
    except TypeError:
        vlans.append('1')

    return vlans

def get_vlan_info(device):
    """Used to retrieve a list with information of all VLANs on a device.

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py

    Returns:
        List of dicts of all VLANs on the switch
    """
    command = 'show vlan brief'
    xml = device.show(command)
    data_dict = xmltodict.parse(xml[1])
    vlan_list = []
    try:
        resource_table = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_vlanbriefxbrief')['ROW_vlanbriefxbrief']
        for each in resource_table:
            temp = {}
            temp['vlan_id'] = str(each.get('vlanshowbr-vlanid', None))
            temp['name'] = str(each.get('vlanshowbr-vlanname', None))
            temp['admin_state'] = str(each.get('vlanshowbr-shutstate', None))
            temp['state'] = str(each.get('vlanshowbr-vlanstate', None))
            if 'None' in str(each.get('vlanshowplist-ifidx', None)):
                temp['interfaces'] = []
            else:
                temp['interfaces'] = interface_range_to_list(
                    str(each.get('vlanshowplist-ifidx', None)))
            vlan_list.append(temp)
    except AttributeError:
        # If only vlan 1 in device NXAPI returns dict instead of list
        temp = {'vlan_id': str(resource_table.get('vlanshowbr-vlanid', None)),
                'name': str(resource_table.get('vlanshowbr-vlanname', None)),
                'admin_state': str(resource_table.get('vlanshowbr-shutstate', None)),
                'state': str(resource_table.get('vlanshowbr-vlanstate', None))}
        if 'None' in str(resource_table.get('vlanshowplist-ifidx', None)):
            temp['interfaces'] = []
        else:
            temp['interfaces'] = interface_range_to_list(
                str(resource_table.get('vlanshowplist-ifidx', None)))
        vlan_list.append(temp)
    return vlan_list

def interface_range_to_list(interfaces):
    """Converts single interface or range of interfaces into a list

    Example:
        Input (interfaces): 'Ethernet1/1,Ethernet1/3-4,Port-channel45'
        Returns: ['Ethernet1/1', 'Ethernet1/3', 'Ethernet1/4', 'Port-channel45' ]

    Args:
        interfaces (str): User input parameter of a interface or range of
        interfaces

    Returns:
        list: list of all interfaces in range
    """
    final = []
    list_of_ranges = []
    if ',' in interfaces:
        list_of_ranges = interfaces.split(',')
    else:
        list_of_ranges.append(interfaces)
    for each in list_of_ranges:
        # check to see if it's a single interface
        if '-' not in each:
            final.append(each)
        else:
            # match physical interface ranges such as Ethernet1/1-3 and
            # Ethernet186/1/1-5
            if '/' in each:
                if_name, _, if_range = each.rpartition('/')
                low = int(if_range.split('-')[0])
                high = int(if_range.split('-')[1])
                for num in range(low, high+1):
                    final.append(if_name + '/' + str(num))
            # match logical interface ranges such as Port-Channel45-47
            else:
                match = re.match(r'(\D+)(\d+-?(\d+)?)', each)
                if_name = match.group(1)
                if_range = match.group(2)
                if '-' in if_range:
                    low = int(if_range.split('-')[0])
                    high = int(if_range.split('-')[1])
                    for num in range(low, high+1):
                        final.append(if_name + str(num))
                else:
                    final.append(if_name + str(if_range))

    return final

def vlan_range_to_list(vlans):
    """Converts single VLAN or range of VLANs into a list

    Example:
        Input (vlans):  2-4,8,10,12-14 OR 3, OR 2,5,10
        Returns: [2,3,4,8,10,12,13,14] OR [3] or [2,5,10]

    Args:
        vlans (str): User input parameter of a VLAN or range of VLANs

    Returns:
        list: ordered list of all VLAN(s) in range

    """
    final = []
    list_of_ranges = []
    if ',' in vlans:
        list_of_ranges = vlans.split(',')
    else:
        list_of_ranges.append(vlans)
    for each in list_of_ranges:
        # check to see if it's a single VLAN (not a range)
        if '-' not in each:
            final.append(each)
        else:
            low = int(each.split('-')[0])
            high = int(each.split('-')[1])
            for num in range(low, high+1):
                vlan = str(num)
                final.append(vlan)

    return final


def _modify_admin_state(value):
    """Internal method used to manipluate admin_state to streamline UX

    Args:
        value (string): should be 'up' or 'down'
            previously, this value was "noshutdown" or "shutdown",
            and changed in the get_vlan method - changed back here
            to help with dev UX

    Returns:
      proper command for admin_state parameter

    ** should never need to be called by user**

    """
    if value == 'up':
        return 'no shutdown'
    elif value == 'down':
        return 'shutdown'


def get_vlan_config_commands(device, vlan, vid):
    """Build command list required for VLAN deployment.

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        vlan (set): parameters to be configured for the given VLAN
        vid (str): VLAN ID to be configured

    Returns:
        list of commands to be configured on the device based on rx'd set

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    vlan = dict(vlan)

    if 'admin_state' in vlan.keys():
        vlan['admin_state'] = _modify_admin_state(vlan['admin_state'])

    VLAN_ARGS = {
        'name': 'name {name}',
        'vlan_state': 'state {vlan_state}',
        'admin_state': '{admin_state}',
        'mode': 'mode {mode}'
    }

    commands = []

    for param, value in vlan.iteritems():
        # The value check is needed, otherwise 'null' is used as a
        # value for 'name'
        # Other option is to pop null/none values from vlan
        command = None
        if value:
            command = VLAN_ARGS.get(param, 'DNE').format(**vlan)
        if command and command != 'DNE':
            commands.append(command)

    commands.insert(0, 'vlan ' + vid)
    commands.append('exit')

    return commands


def get_remove_vlan_commands(device, vid):
    """Build command list required to remove VLAN.

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        vid (str): VLAN ID to be removed

    Returns:
        list of commands required to remove VLAN

    """
    commands = ['no vlan ' + vid]
    return commands


def is_default(device, interface):
    """Checks to see if interface exists and if it is a default config

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        interface (str): full name of interface, i.e. vlan10,
            Ethernet1/1, loopback10

    Returns:
        True: if interface has default config
        False: if it does not have a default config
        DNE (str): if the interface does not exist - loopbacks, SVIs, etc.

    """
    command = 'show run interface ' + interface
    try:
        data = device.show(command, text=True)
        data_dict = xmltodict.parse(data[1])
        raw_intf = data_dict['ins_api']['outputs']['output']['body']
        raw_list = raw_intf.split('\n')
        if raw_list[-1].startswith('interface'):
            return True
        else:
            return False
    except (KeyError, CLIError):
        # 'body' won't be there if interface doesn't exist
        # logical interface does not exist
        return 'DNE'


def get_interface_type(interface):
    """Gets the type of interface

    Args:
        interface (str): full name of interface, i.e. Ethernet1/1, loopback10,
            port-channel20, vlan20

    Returns:
        type of interface: ethernet, svi, loopback, management, portchannel,
         or unknown

    """
    if interface.upper().startswith('ET'):
        return 'ethernet'
    elif interface.upper().startswith('VL'):
        return 'svi'
    elif interface.upper().startswith('LO'):
        return 'loopback'
    elif interface.upper().startswith('MG'):
        return 'management'
    elif interface.upper().startswith('MA'):
        return 'management'
    elif interface.upper().startswith('PO'):
        return 'portchannel'
    else:
        return 'unknown'


def get_manual_interface_attributes(device, interface):
    """Gets admin state and description of a SVI interface

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        interface (str): full name of SVI interface, i.e. vlan10

    Returns:
        dictionary that has two k/v pairs: admin_state & description
            if not an svi, returns None

    """
    if get_interface_type(interface) == 'svi':
        command = 'show running interface ' + interface
        try:
            get_data = device.show(command, text=True)
            data_dict = xmltodict.parse(get_data[1])
            show_command = data_dict['ins_api']['outputs']['output']['body']
        except (KeyError, CLIError):
            return None

        if show_command:
            command_list = show_command.split('\n')
            desc = None
            admin_state = 'down'
            for each in command_list:
                if 'description' in each:
                    my_line = each.split('description')
                    desc = my_line[1].strip()
                elif 'no shutdown' in each:
                    admin_state = 'up'
            return dict(description=desc, admin_state=admin_state)
    else:
        return None


def get_interface_speed(speed):
    """Translates speed into bits/sec given the output from the API

    Args:
        speed (string): input should be from NX-API in the form of '10 Gb/s'-
            param being sent should be "eth_speed" from output from
            'show interface eth x/y' in NX-API

    Returns:
        equivalent speed (str) in bits per second or "auto"

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    if speed.startswith('auto'):
        return 'auto'
    elif speed.startswith('40'):
        return '40000'
    elif speed.startswith('100 G'):
        return '100000'
    elif speed.startswith('10'):
        return '10000'
    elif speed.startswith('1'):
        return '1000'
    elif speed.startswith('100 M'):
        return '100'


def get_interface(device, intf):
    """Gets current config/state of interface

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        intf (string): full name of interface, i.e. Ethernet1/1, loopback10,
            port-channel20, vlan20

    Returns:
      dictionary that has relevant config/state data about the given
          interface based on the type of interface it is

    """
    command = 'show interface ' + intf
    intf_type = get_interface_type(intf)
    interface = {}
    try:
        data = device.show(command)
        data_dict = xmltodict.parse(data[1])
        i = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_interface')['ROW_interface']
    except (KeyError, AttributeError, CLIError):
        i = {}

    if i:
        interface['interface'] = str(i['interface'])
        interface['type'] = intf_type
        if intf_type == 'ethernet':
            interface['admin_state'] = str(i.get('admin_state',
                                                 'unable_to_get_n3K_api_bug'))
            interface['state'] = str(i.get('state', 'error'))
            interface['description'] = str(i.get('desc', None))
            interface['duplex'] = str(i.get('eth_duplex', 'error'))
            interface['mac_address'] = str(i.get('eth_hw_addr', 'error'))
            speed = str(i.get('eth_speed', 'error'))
            if speed != 'error':
                interface['speed'] = get_interface_speed(speed)
            interface['mode'] = str(i.get('eth_mode', 'layer3'))
            if interface['mode'] == 'access' or interface['mode'] == 'trunk':
                interface['mode'] = 'layer2'
            elif interface['mode'] == 'routed':
                interface['mode'] = 'layer3'
        elif intf_type == 'svi':
            interface['state'] = str(i.get('svi_line_proto', 'error'))
            # interface['admin_state'] = str(i.get('svi_admin_state',
            #                                'error'))
            # interface['description'] = str(i.get('desc',
            #                                'unable_to_read'))

            # Using manual process to fix possible bugs or lack of info via API
            attributes = get_manual_interface_attributes(device, intf)
            interface['admin_state'] = str(attributes.get('admin_state',
                                                          'error'))
            interface['description'] = str(attributes.get('description',
                                                          'unable_to_read_ + '
                                                          ' nxapi_bug'))

        elif intf_type == 'loopback':
            interface['admin_state'] = str(i.get('state', 'error'))
            interface['description'] = str(i.get('desc', None))
        elif intf_type == 'management':
            interface['admin_state'] = str(i.get('state', 'error'))
            interface['description'] = str(i.get('desc', None))
            interface['duplex'] = str(i.get('eth_duplex', 'error'))
            interface['speed'] = str(i.get('eth_speed', 'error'))
        elif intf_type == 'portchannel':
            interface['description'] = str(i.get('desc', None))
            interface['admin_state'] = str(i.get('admin_state', None))
            interface['state'] = str(i.get('state', None))
            interface['duplex'] = str(i.get('eth_duplex', 'error'))
            interface['speed'] = str(i.get('eth_speed', 'error'))
            interface['mode'] = str(i.get('eth_mode', 'layer3'))
            if interface['mode'] == 'access' or interface['mode'] == 'trunk':
                interface['mode'] = 'layer2'

    return interface


def get_interfaces_dict(device):
    """Gets all active interfaces on a given switch

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py

    Returns:
        dictionary with interface type (ethernet,svi,loop,portchannel) as the
            keys.  Each value is a list of interfaces of given interface (key)
            type.

    """
    command = 'show interface status'
    data = device.show(command)
    data_dict = xmltodict.parse(data[1])
    interfaces = {
        'ethernet': [],
        'svi': [],
        'loopback': [],
        'management': [],
        'portchannel': [],
        'unknown': []
        }

    interface_list = data_dict['ins_api']['outputs']['output']['body'].get(
        'TABLE_interface')['ROW_interface']
    for i in interface_list:
        intf = i['interface']
        intf_type = get_interface_type(intf)

        interfaces[intf_type].append(intf)

    return interfaces


def get_intf_args(interface):
    """Gets arguments/commands valid for a given interface/type

    Args:
        interface (str): full name of interface, i.e. Ethernet1/1

    Returns:
        dictionary: maps config option to associated command

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    intf_type = get_interface_type(interface)

    arguments = {'admin_state': '', 'description': 'description {description}'}
    if intf_type == 'ethernet':
        arguments['duplex'] = 'duplex {duplex}'
        arguments['speed'] = 'speed {speed}'
        arguments['mode'] = ''
    elif intf_type == 'management':
        arguments['duplex'] = 'duplex {duplex}'
        arguments['speed'] = 'speed {speed}'
    elif intf_type == 'portchannel':
        arguments['mode'] = ''
    elif intf_type == 'loopback' or intf_type == 'svi':
        pass

    return arguments


def get_interface_config_commands(device, interface, intf):
    """Generates list of commands to configure on device

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        interface (str): k/v pairs in the form of a set that should
            be configured on the device
        intf (str): full name of interface, i.e. Ethernet1/1

    Returns:
      list: ordered list of commands to be sent to device

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    INTERFACE_ARGS = get_intf_args(intf)

    commands = []
    interface = dict(interface)
    for attribute, value in interface.iteritems():
        command = None
        if attribute == 'admin_state':
            if value == 'up':
                command = 'no shutdown'
            elif value == 'down':
                command = 'shutdown'
        elif attribute == 'mode':
            if value == 'layer2':
                command = 'switchport'
            elif value == 'layer3':
                command = 'no switchport'
        elif attribute == 'description':
            command = 'description {description}'.format(**interface)
        else:
            if attribute == 'speed':
                command = 'speed {speed}'.format(**interface)
            elif attribute == 'duplex':
                command = 'duplex {duplex}'.format(**interface)

        if command:
            if attribute == 'speed':
                commands.insert(0, command)
            else:
                commands.append(command)

    commands.insert(0, 'interface ' + intf)

    return commands


def default_interface(device, interface):
    """Generates list of command(s) to default an interface

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        interface (str): full name of interface, i.e. Ethernet1/1

    Returns:
        list: currently returns list of 1

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    TODO: Remove device param from being used

    """
    commands = []
    commands.append('default interface ' + interface)
    return commands


def remove_interface(device, interface):
    """Generates list of command(s) to remove a logical an interface

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        interface (string): full name of logical interface, i.e. vla10,
            loopback10, port-channel20

    Returns:
        list: currently returns list of 1

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    TODO: Remove device param from being used

    """
    commands = []
    commands.append('no interface ' + interface)
    return commands


def get_ipv4_interface(device, intf):
    """Gets IPv4 interface config for existing Layer 3 interfaces

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        intf (string): full name of logical interface, i.e. vla10,
            loopback10, port-channel20

    Returns:
      dictionary: returns params/values of an existing L3 interface,
          i.e. IP, mask, VRF, etc.

    """
    command = 'show ip interface ' + intf
    interface = {}
    get_data = {}
    try:
        data = device.show(command)
        data_dict = xmltodict.parse(data[1])
        get_data = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_intf')['ROW_intf']
        try:
            v_data = data_dict['ins_api']['outputs']['output']['body']
            vrfdata = v_data['TABLE_vrf']['ROW_vrf']
        except KeyError:
            vrfdata = {}
    except (KeyError, AttributeError, CLIError):
        interface = {}

    interface['interface'] = intf
    interface['type'] = get_interface_type(intf)
    interface['ip_addr'] = str(get_data.get('prefix', None))
    interface['mask'] = str(get_data.get('masklen', None))
    interface['subnet'] = str(get_data.get('subnet', None))
    interface['vrf'] = str(vrfdata.get('vrf-name-out', 'default'))

    return interface


def get_config_ipv4_commands(delta, interface, existing):
    """Returns list of commands to be configured on a Layer 3 interface

    Args:
        delta (set): params to be configured
        interface (string): full name of logical interface,
            i.e. vla10, loopback10, port-channel20
        existing (dict): object created in the module that is from
           get_ipv4_interface() module

    Returns:
      list: ordered list of commands to be configured on the
       switch to get interface into desired state

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    commands = []
    delta = dict(delta)

    # loop used in the situation that just an IP address or just a
    # mask is changing, not both.
    for each in ['ip_addr', 'mask']:
        if each not in delta.keys():
            delta[each] = existing[each]

    command = 'ip address {ip_addr}/{mask}'.format(**delta)
    commands.append(command)
    commands.insert(0, 'interface ' + interface)

    return commands


def get_remove_ipv4_config_commands(existing, interface):
    """Returns list of commands to be configured on a Layer 3 interface

    Args:
        existing (dict): object from get_ipv4_interface modules
        interface (string): full name of logical interface, i.e. vla10,
           loopback10, port-channel20

    Returns:
        list: ordered list of commands to be configured on the switch
           to get interface into desired state that will remove an
           IP address and/or subnet mask

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    commands = []
    commands.append('interface ' + interface)
    commands.append('no ip address')

    return commands


def get_interface_mode(device, interface):
    """Gets current mode of interface: layer2 or layer3

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        interface (string): full name of interface, i.e. Ethernet1/1,
            loopback10, port-channel20, vlan20

    Returns:
        str: 'layer2' or 'layer3'

    """
    command = 'show interface ' + interface
    intf_type = get_interface_type(interface)
    interface = {}
    mode = 'unknown'
    try:
        data = device.show(command)
        data_dict = xmltodict.parse(data[1])
        i = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_interface')['ROW_interface']
    except (KeyError, AttributeError, CLIError):
        i = {}
    if i:
        if intf_type in ['ethernet', 'portchannel']:
            mode = str(i.get('eth_mode', 'layer3'))
            if mode == 'access' or mode == 'trunk':
                mode = 'layer2'
        elif intf_type == 'loopback' or intf_type == 'svi':
            mode = 'layer3'
    return mode


def interface_is_portchannel(device, interface):
    """Checks to see if an interface is part of portchannel bundle

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        interface (str): full name of interface, i.e. Ethernet1/1

    Returns:
        True/False based on if interface is a member of a portchannel bundle

    """
    intf_type = get_interface_type(interface)
    if intf_type == 'ethernet':
        command = 'show interface ' + interface
        try:
            data = device.show(command)
            data_dict = xmltodict.parse(data[1])
            interface = data_dict['ins_api']['outputs']['output']['body'].get(
                'TABLE_interface')['ROW_interface']
        except (KeyError, AttributeError, CLIError):
            interface = None
        if interface:
            state = interface.get('eth_bundle', None)
            if state:
                return True
            else:
                return False

    return False


def get_switchport(device, port):
    """Gets current config of L2 switchport

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        port (str): full name of interface, i.e. Ethernet1/1

    Returns:
        dictionary with k/v pairs for L2 vlan config

    """

    command = 'show interface {0} switchport'.format(port)
    # The command being used here is 'show interface switcport'
    # It executes this, retrieves all interfaces, and then returns
    # the given interface when a match occurs.
    # Ideally, this command would support
    #  'show interface switcport Ethernet1/1'
    # in order to reduce the time required to check a switcport configuration

    data = device.show(command)
    data_dict = xmltodict.parse(data[1])
    switchport = {}
    try:
        port_out = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_interface')['ROW_interface']
        switchport['interface'] = str(port_out['interface'])
        switchport['mode'] = str(port_out['oper_mode'])
        switchport['switchport'] = str(port_out['switchport'])
        switchport['access_vlan'] = str(port_out['access_vlan'])
        switchport['access_vlan_name'] = str(port_out['access_vlan_name'])
        switchport['native_vlan'] = str(port_out['native_vlan'])
        switchport['native_vlan_name'] = str(port_out['native_vlan_name'])
        switchport['trunk_vlans'] = str(port_out['trunk_vlans'])
    except (KeyError, AttributeError):
        return switchport

    return switchport


def get_switchport_config_commands(device, switchport, port):
    """Gets commands required to config a given switchport interface

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        switchport (set): parameters to be configured (from Ansible module)
        port (str): full name of interface to be configured, i.e. Ethernet1/1

    Returns:
        list: ordered list of commands to be sent to device

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    CONFIG_ARGS = {
        'mode': 'switchport mode {mode}',
        'access_vlan': 'switchport access vlan {access_vlan}',
        'native_vlan': 'switchport trunk native vlan {native_vlan}',
        'trunk_vlans': 'switchport trunk allowed vlan {trunk_vlans}',
    }

    commands = []
    switchport = dict(switchport)
    for param, value in switchport.iteritems():
        command = CONFIG_ARGS.get(param, 'DNE').format(**switchport)
        if command and command != 'DNE':
            commands.append(command)

    commands.insert(0, 'interface ' + port)

    return commands


def clean_up_interface_vlan_configs(proposed, existing):
    """Removes unecessary and unused configs
       i.e. removes access vlan configs if a trunk port is being configured
       or removes trunk port/vlan configs if access vlan is being configured

    Args:
        proposed (dict): proposed configuration params & values
        existing (dict): existing as-is configuration params & values
        both args are being sent from the Ansible module

    Returns:
        list: ordered list of commands to be sent to device

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    commands = []
    if proposed['mode'] == 'access':
        if existing['native_vlan'] != '1':
            commands.append('no switchport trunk native vlan')
        if existing['trunk_vlans'] != '1-4094':
            commands.append('no switchport trunk allowed vlan')
        if existing['mode'] == 'trunk':
            commands.append('no switchport mode trunk')
    elif proposed['mode'] == 'trunk':
        if existing['mode'] == 'access':
            commands.append('no switchport access vlan')
    if commands:
        commands.insert(0, 'interface ' + proposed['interface'])

    return commands


def is_switchport_default(existing):
    """Determines if switchport has a default config based on mode

    Args:
        existing (dict): existing switcport configuration from Ansible mod

    Returns:
        boolean: True if access port and access vlan = 1 or
                 True if trunk port and native = 1 and trunk vlans = 1-4094
                 else False

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """

    default = False
    mode = existing['mode']
    if mode == 'access':
        if existing['access_vlan'] == '1':
            default = True
    elif mode == 'trunk':
        if existing['native_vlan'] == '1':
            if existing['trunk_vlans'] == '1-4094':
                default = True
    return default


def remove_switchport_config(device, switchport, port):
    """Gets commands required to remove a config from a given switchport interface

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        switchport (dict): parameters to be unconfigured (from Ansible mod)
        port (string): full name of interface to be config'd, i.e. Ethernet1/1

    Returns:
        list: ordered list of commands to be sent to device

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    CONFIG_ARGS = {
        'mode': 'no switchport mode {mode}',
        'access_vlan': 'no switchport access vlan {access_vlan}',
        'native_vlan': 'no switchport trunk native vlan {native_vlan}',
        'trunk_vlans': 'no switchport trunk allowed vlan {trunk_vlans}',
        }

    commands = []

    for param, value in switchport.iteritems():
        if param == 'mode' and value == 'access':
            # this is making it so that 'no switchport mode access' is added
            # to command list
            # although it wouldn't necessarily hurt the config by any means.
            command = None
        else:
            command = CONFIG_ARGS.get(param, 'DNE').format(**switchport)
        if command and command != 'DNE':
            commands.append(command)

    commands.insert(0, 'interface ' + port)

    return commands


def get_min_links(device, group):
    """Checks to see if min-links are configured, if so, returns the config'd value

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        group (str): port-channel group ID/number

    Returns:
      str: value of min-links, if set
          else returns None (if min-links is not configured)

    """
    command = 'show run interface port-channel' + group
    minlinks = None
    data = device.show(command, text=True)
    data_dict = xmltodict.parse(data[1])
    ml_data = data_dict['ins_api']['outputs']['output']['body']
    ml_list = ml_data.split('\n')
    for line in ml_list:
        this_line = line.strip()
        if 'min-links' in this_line:
            minlinks = this_line.split('min-links ')[-1]
    return minlinks


def get_portchannel_members(pchannel):
    """Gets the members of an existing portchannel

    Args:
        pchannel (dict): port-channel dict

    Returns:
        list: empty if currently no members, otherwise
            list of Ethernet interfaces that make up
            the given port-channel

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    try:
        members = pchannel['TABLE_member']['ROW_member']
    except KeyError:
        members = []

    return members


def get_portchannel(device, group):
    """Gets existing config state of the portchannel

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        group (str): port-channel group ID

    Returns:
      dict: params/values of the given portchannel
           includes: members, min_links, mode, etc.

    """
    command = 'show port-channel summary interface port-channel ' + group
    pchannel = {}
    portchannel = {}

    try:
        data = device.show(command)
        data_dict = xmltodict.parse(data[1])
        pchannel = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_channel')['ROW_channel']
    except (KeyError, AttributeError, CLIError):
        pchannel = {}

    member_dictionary = {}
    if pchannel:
        portchannel['group'] = str(pchannel['group'])
        # LACP or None (it is None when no interfaces are in PC or
        # mode set to ON)
        proto = str(pchannel['prtcl'])
        members_list_of_dict = get_portchannel_members(pchannel)
        members = []
        # try/except needed bc it's a list of dicts if there is more than 1
        # if there isn't, it's just a single dict
        # This is common for NX-API
        try:
            for each in members_list_of_dict:
                interface = str(each['port'])
                members.append(interface)

                temp = {}
                temp['status'] = str(each['port-status'])
                temp['mode'] = get_portchannel_mode(device, interface, proto)

                member_dictionary[interface] = temp

        except TypeError:
            interface = str(members_list_of_dict['port'])
            members.append(interface)
            temp = {}
            temp['status'] = str(members_list_of_dict['port-status'])
            temp['mode'] = get_portchannel_mode(device, interface, proto)

            member_dictionary[interface] = temp

        # Each member should have the same mode
        # This is just to verify that.
        modes = set()
        for each, value in member_dictionary.iteritems():
            modes.update([value['mode']])
        if len(modes) == 1:
            portchannel['mode'] = value['mode']
        else:
            portchannel['mode'] = 'unknown'

        portchannel['members'] = members
        portchannel['members_detail'] = member_dictionary
        portchannel['min_links'] = str(get_min_links(device, group))

    return portchannel


def get_portchannel_mode(device, intf, proto):
    """Gets existing mode (on, active, passive) of physical interface

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        intf (str): full name of Ethernet interace
        proto (str): 'LACP', 'None', or 'on'

    Returns:
        str: 'on,' 'passive', 'active'

    """
    if proto != 'LACP':
        mode = 'on'
    else:
        command = 'show run interface ' + intf
        mode = 'Unknown'

        data = device.show(command, text=True)
        data_dict = xmltodict.parse(data[1])
        mode_data = data_dict['ins_api']['outputs']['output']['body']

        mode_list = mode_data.split('\n')
        for line in mode_list:
            this_line = line.strip()
            if this_line.startswith('channel-group'):
                find = this_line
        if 'mode' in find:
            if 'passive' in find:
                mode = 'passive'
            elif 'active' in find:
                mode = 'active'
    return mode


def get_portchannel_list(device):
    """Gets list of active port-channels on a device

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
    Returns:
        list: contains the group numbers of all port-channels

    """
    command = 'show port-channel summary'
    portchannels = []
    pc_list = []
    try:
        data = device.show(command)
        data_dict = xmltodict.parse(data[1])
        pc_list = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_channel')['ROW_channel']
    except (KeyError, AttributeError):
        pass
    if pc_list:
        try:
            for each in pc_list:
                portchannels.append(each['group'])
        except TypeError:
            portchannels.append(pc_list['group'])
    return portchannels


def get_commands_to_add_members(proposed, existing):
    """Gets commands required to add members to an existing port-channel

    Args:
        existing (dict): existing config as defined in nxos_portchannel
        proposed (dict): proposed config as defined in nxos_portchannel

    Returns:
        list: ordered list of commands to be sent to device to add members to
            a port-channel

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    proposed_members = proposed['members']
    existing_members = existing['members']

    members_to_add = set(proposed_members).difference(existing_members)
    members_to_add_list = list(members_to_add)

    commands = []

    if members_to_add_list:
        for member in members_to_add_list:
            commands.append('interface ' + member)
            commands.append('channel-group {0} mode {1}'.format(
                existing['group'], proposed['mode']))

    return commands


def get_commands_to_remove_members(proposed, existing):
    """Gets commands required to remove members from an existing port-channel

    Args:
        existing (dict): existing config as defined in nxos_portchannel
        proposed (dict): proposed config as defined in nxos_portchannel

    Returns:
        list: ordered list of commands to be sent to device to remove members
            of a port-channel

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    proposed_members = proposed['members']
    existing_members = existing['members']

    members_to_remove = set(existing_members).difference(proposed_members)
    members_to_remove_list = list(members_to_remove)

    commands = []
    if members_to_remove_list:
        for member in members_to_remove_list:
            commands.append('interface ' + member)
            commands.append('no channel-group {0}'.format(existing['group']))

    return commands


def get_commands_if_mode_change(proposed, existing, group, mode):
    """Gets commands required to modify mode of a port-channel
        Note: requires removing existing config and re-config'ing new
        port-channel with new mode

    Args:
        existing (dict): existing config as defined in nxos_portchannel
        proposed (dict): proposed config as defined in nxos_portchannel
        group (str):  port-channel group number
        mode (str): on, active, or passive

    Returns:
        list: ordered list of cmds to be sent to device for a change in mode

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    proposed_members = proposed['members']
    existing_members = existing['members']

    members_to_remove = set(existing_members).difference(proposed_members)
    members_to_remove_list = list(members_to_remove)

    members_dict = existing['members_detail']
    members_with_mode_change = []

    for interface, values in members_dict.iteritems():
        if interface in proposed_members \
                and (interface not in members_to_remove_list):
            # Could probabaly make an assumption after checking one instead
            if values['mode'] != mode:
                members_with_mode_change.append(interface)
    commands = []
    if members_with_mode_change:
        for member in members_with_mode_change:
            commands.append('interface ' + member)
            commands.append('no channel-group ' + group)

        for member in members_with_mode_change:
            commands.append('interface ' + member)
            commands.append('channel-group {0} mode {1}'.format(group, mode))
    return commands


def config_portchannel(proposed, mode, group):
    """Gets commands required to configure net new port-channels
        Not used if a modification is being made.

    Args:
        proposed (dict): proposed config as defined in nxos_portchannel
        mode (str): on, active, or passive
        group (str):  port-channel group number

    Returns:
      list: ordered list of commands to be sent to device for net
          new port-channel configuration

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    CONFIG_ARGS = {
        'mode': 'channel-group {group} mode {mode}',
        'min_links': 'lacp min-links {min_links}',
    }
    commands = []

    for member in proposed.get('members', []):
        commands.append('interface ' + member)
        commands.append(CONFIG_ARGS.get('mode').format(group=group, mode=mode))

    min_links = proposed.get('min_links', None)
    if min_links:
        command = 'interface port-channel {group}'.format(group=group)
        commands.append(command)
        commands.append(CONFIG_ARGS.get('min_links').format(
            min_links=min_links))

    return commands


def get_commands_min_links(existing, proposed, group, min_links):
    """Gets commands required to config min links for existing port-channels

    Args:
        existing (dict): existing config as defined in nxos_portchannel
        proposed (dict): proposed config as defined in nxos_portchannel
        group (str):  port-channel group
        min_links (str): min-links value to be configured

    Returns:
        list: ordered list of cmds to be sent to device for min-links config

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    commands = []
    if not existing['min_links'] \
            or (existing['min_links'] != proposed['min_links']):
        commands.append('interface port-channel' + group)
        commands.append('lacp min-link ' + min_links)
    return commands


def get_commands_to_remove_portchannel(device, group):
    """Gets commands required to remove a port channel

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        group (str): port-channel group number/ID

    Returns:
        list: ordered list of commands to be sent to device

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    commands = []
    commands.append('no interface port-channel' + group)
    return commands


def get_interface_running_config(device, interface):
    """Gets equiv to show run interface Eth1/1

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        interface (str): full name of interface, i.e. vlan10,
            Ethernet1/1, loopback10

    Returns:
        list: each element is a line of config starting
            with interface name x/y

    """
    command = 'show run interface ' + interface
    try:
        data = device.show(command, text=True)
        data_dict = xmltodict.parse(data[1])
        raw_intf = data_dict['ins_api']['outputs']['output']['body']
        raw_list = raw_intf.split('\n')
        final_list = []
        for each in raw_list[5:]:
            final_list.append(str(each).strip())
    except (KeyError, CLIError):
        return 'error'
    return final_list


def get_vrf_list(device):
    """Gets base configuration of a given VRF

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py

    Returns:
      dict: params are vrf (name), state, and description

    """
    command = 'show vrf all'
    vrf_table = None

    try:
        data = device.show(command)
        data_dict = xmltodict.parse(data[1])
        vrf_table = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_vrf')['ROW_vrf']
    except (KeyError, AttributeError):
        return []

    vrf_list = []
    if vrf_table:
        for each in vrf_table:
            vrf_list.append(str(each['vrf_name'].lower()))

    return vrf_list


def get_vrf_description(device, vrf):
    """Gets description of configured VRF.

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        vrf: case-sensitive VRF (because 'show run section $VRF' is being used)

    Returns:
        str: if description is set, otherwise returns None

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    command = 'show run section vrf | begin {0}'.format(vrf) \
              + ' | include description'

    description = None
    try:
        data = device.show(command, text=True)
        data_dict = xmltodict.parse(data[1])
        get_data = data_dict['ins_api']['outputs']['output']['body']
        if get_data:
            full_line = get_data.strip()
            if full_line.startswith('descr'):
                description = full_line.split('description')[1].strip()
        else:
            description = None
    except (KeyError, CLIError):
        description = None

    return description


def get_vrf(device, vrf):
    """Gets base configuration of a given VRF

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        vrf (str): vrf name

    Returns:
        dict: params are vrf (name), state, and description

    """
    command = 'show vrf ' + vrf
    vrf = {}
    get_data = None

    try:
        data = device.show(command)
        data_dict = xmltodict.parse(data[1])
        get_data = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_vrf')['ROW_vrf']
    except (KeyError, AttributeError, CLIError):
        return vrf

    if get_data:
        vrf['vrf'] = str(get_data['vrf_name'])
        vrf['admin_state'] = str(get_data['vrf_state']).lower()
        vrf['description'] = str(get_vrf_description(device, vrf['vrf']))

    return vrf


def get_commands_to_remove_vrf(vrf):
    """Gets commands to remove a VRF
       Note: Does not remove interface level configurations

    Args:
        vrf (str): vrf name

    Returns:
        list: ordered list to remove vrf config

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.
    """
    commands = []
    commands.append('no vrf context ' + vrf)
    return commands


def get_commands_to_config_vrf(delta, vrf):
    """Gets commands to configure a VRF

    Args:
        delta (set): params to be config'd- created in nxos_vrf
        vrf (str): vrf name

    Returns:
        list: ordered list to config a vrf

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.
    """
    commands = []
    for param, value in delta:
        command = None
        if param == 'description':
            command = 'description ' + value
        elif param == 'admin_state':
            if value.lower() == 'up':
                command = 'no shutdown'
            elif value.lower() == 'down':
                command = 'shutdown'
        if command:
            commands.append(command)
    if commands:
        commands.insert(0, 'vrf context ' + vrf)
    return commands


def get_commands_to_config_vpc(vpc, domain, existing):
    """Gets commands to configure a VPC global config params

    Args:
        vpc (set): params to be config'd- created in nxos_vpc
        domain (str): VPC domain ID being configured
        existing (dict): params of existing vpc config- from nxos_vpc

    Returns:
        list: ordered list to config a vrf

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.
    """
    vpc = dict(vpc)

    domain_only = vpc.get('domain', None)
    pkl_src = vpc.get('pkl_src', None)
    pkl_dest = vpc.get('pkl_dest', None)
    pkl_vrf = vpc.get('pkl_vrf', None)
    if not pkl_vrf:
        vpc['pkl_vrf'] = existing['pkl_vrf']

    commands = []
    if pkl_src and pkl_dest:
        pkl_command = 'peer-keepalive destination {pkl_dest}'.format(**vpc) \
                      + ' source {pkl_src} vrf {pkl_vrf}'.format(**vpc)
        commands.append(pkl_command)
    elif pkl_vrf:
        # this will be true if there is NO change in source/dest IPs,
        # but there is a change in VRF
        # It's probably unlikely this will be used, but gives the option to
        # not have to remove and re-add the VPC
        pkl_src = existing.get('pkl_src', None)
        pkl_dest = existing.get('pkl_dest', None)
        if pkl_src and pkl_dest:
            pkl_command = 'peer-keepalive destination {0}'.format(pkl_dest) \
                          + ' source {1} vrf {2}'.format(pkl_src, pkl_vrf)
            commands.append(pkl_command)

    if vpc.get('auto_recovery', None) == False:
        vpc['ar'] = 'no'
    else:
        vpc['ar'] = ''

    if vpc.get('peer_gw', None) == False:
        vpc['pg'] = 'no'
    else:
        vpc['pg'] = ''

    CONFIG_ARGS = {
        'role_priority': 'role priority {role_priority}',
        'system_priority': 'system-priority {system_priority}',
        'delay_restore': 'delay restore {delay_restore}',
        'peer_gw': '{pg} peer-gateway',
        'auto_recovery': '{ar} auto-recovery',
        }

    for param, value in vpc.iteritems():
        command = CONFIG_ARGS.get(param, 'DNE').format(**vpc)
        if command and command != 'DNE':
            commands.append(command.strip())
        command = None

    if commands or domain_only:
        commands.insert(0, 'vpc domain ' + domain)
    return commands


def get_autorecovery(auto):
    """Internal function checking auto_recovery status

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.
    """
    ar = auto.split(' ')[0]
    if ar.lower() == 'enabled':
        return True
    else:
        return False


def get_vpc(device):
    """Gets vpc config from network switch

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py

    Returns:
        dict: k/v pairs of vpc config params

    """
    vpc = {}

    # ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###
    # Obtaining VPC domain ID and auto-recovery status
    command = 'show vpc'
    vpc_dict = {}
    try:
        data = device.show(command)
        data_dict = xmltodict.parse(data[1])
        vpc_dict = data_dict['ins_api']['outputs']['output']['body']
    except KeyError:
        domain = None
        auto_recovery = None

    if vpc_dict:
        domain = str(vpc_dict['vpc-domain-id'])
        auto_recovery = get_autorecovery(str(
            vpc_dict['vpc-auto-recovery-status']))

    if domain != 'not configured':

        # ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###
        # Obtaining VPC system priority, role priority, delay restore,
        # pkl_src, and peer_gw
        delay_restore = None
        pkl_src = None
        role_priority = None
        system_priority = None

        run = get_vpc_running_config(device)
        peer_gw = False
        if run:
            vpc_list = run.split('\n')
            for each in vpc_list:
                if 'delay restore' in each:
                    my_line = each.split(' ')
                    if len(my_line) == 5:
                        value = my_line[-1]
                        delay_restore = value
                elif 'peer-keepalive destination' in each:
                    my_line = each.split(' ')
                    for word in my_line:
                        if 'source' in word:
                            index = my_line.index(word)
                            pkl_src = my_line[index+1]
                elif 'role priority' in each:
                    my_line = each.split(' ')
                    value = my_line[-1]
                    role_priority = value
                elif 'system-priority' in each:
                    my_line = each.split(' ')
                    value = my_line[-1]
                    system_priority = value
                elif 'peer-gateway' in each:
                    peer_gw = True

        # # ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###
        # Obtaining pkl_dest and pkl_vrf
        command = 'show vpc peer-keepalive'
        try:
            data = device.show(command)
            data_dict = xmltodict.parse(data[1])
            vpc_dict = data_dict['ins_api']['outputs']['output']['body']
        except (KeyError, CLIError):
            pkl_dest = None
            pkl_vrf = None

        if vpc_dict:
            # WHY IS THIS RETURNING A LIST????
            pkl_dest = vpc_dict['vpc-keepalive-dest']
            if pkl_dest == 'N/A' or 'N/A' in pkl_dest:
                pkl_dest = None
            elif len(pkl_dest) == 2:
                pkl_dest = pkl_dest[0]
            pkl_vrf = str(vpc_dict['vpc-keepalive-vrf'])

        # ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### #

        vpc['domain'] = domain
        vpc['auto_recovery'] = auto_recovery
        vpc['delay_restore'] = delay_restore
        vpc['pkl_src'] = pkl_src
        vpc['role_priority'] = role_priority
        vpc['system_priority'] = system_priority
        vpc['pkl_dest'] = pkl_dest
        vpc['pkl_vrf'] = pkl_vrf
        vpc['peer_gw'] = peer_gw
    else:
        vpc = {}

    return vpc


def get_portchannel_vpc_config(device, portchannel):
    """Gets vpc config from network switch

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        portchannel (str): group number of the portchannel, i.e. 10, 20, etc.
            NOT including "port-channel"

    Returns:
        str: vpc group number that exists on that given portchannel
            or 'peer-link', if the portchannel is the peer-link

    """
    command = 'show vpc brief'

    peer_link_pc = None

    try:
        data = device.show(command)
        data_dict = xmltodict.parse(data[1])
        table = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_peerlink')['ROW_peerlink']
    except (KeyError, AttributeError, TypeError):
        table = None

    if table:
        peer_link_pc = table.get('peerlink-ifindex', None)

    if peer_link_pc:
        plpc = str(peer_link_pc[2:])
        if portchannel == plpc:
            return 'peer-link'

    mapping = get_existing_portchannel_to_vpc_mappings(device)
    for vpc, port_channel in mapping.iteritems():
        port_ch = str(port_channel[2:])
        if port_ch == portchannel:
            return str(vpc)
    return None


def get_commands_to_remove_vpc_interface(portchannel, config_value):
    """Gets commands to remove a vpc config from a portchannel

    Args:
        portchannel (str): group number of the portchannel
        config_value (str): 'peer-link' or vpc number

    Returns:
        str: vpc group number that exists on that given portchannel
            or 'peer-link', if the portchannel is the peer-link

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    commands = []
    command = 'no vpc ' + config_value
    commands.append(command)
    commands.insert(0, 'interface port-channel' + portchannel)
    return commands


def get_commands_to_config_vpc_interface(portchannel, config_value):
    """Gets commands to config a vpc or peerlink on a portchannel

    Args:
        portchannel (str): group number of the portchannel
        config_value (str): 'peer-link' or vpc number

    Returns:
        list: ordered list of commands to configure device

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    commands = []
    command = 'vpc ' + config_value
    commands.append(command)
    commands.insert(0, 'interface port-channel' + portchannel)
    return commands


def get_active_vpc_peer_link(device):
    """Gets portchannel that is the active peerlink

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py

    Returns:
        str: port-channel interface that is the active peerlink

    """
    command = 'show vpc brief'
    try:
        data = device.show(command)
        data_dict = xmltodict.parse(data[1])
        peer_link = str(data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_peerlink')['ROW_peerlink']['peerlink-ifindex'])
    except (KeyError, AttributeError):
        peer_link = None

    return peer_link


def get_existing_portchannel_to_vpc_mappings(device):
    """Gets mapping for vpc to portchannels

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py

    Returns:
        dict: k/v pairs in the form of vpc/pc

    """
    command = 'show vpc brief'
    try:
        data = device.show(command)
        data_dict = xmltodict.parse(data[1])
        table = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_vpc')['ROW_vpc']
    except (KeyError, AttributeError, TypeError):
        table = None
    pc_vpc_mapping = {}
    if table:

        try:
            for each in table:
                pc_vpc_mapping[str(each['vpc-id'])] = str(each['vpc-ifindex'])
        except TypeError:
            pc_vpc_mapping[str(table['vpc-id'])] = str(table['vpc-ifindex'])
    return pc_vpc_mapping


def get_vpc_running_config(device):
    """Gets vpc running config

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py

    Returns:
        str: 'show run section vpc'

    """
    command = 'show running section vpc'
    try:
        get_data = device.show(command, text=True)
        data_dict = xmltodict.parse(get_data[1])
        data = data_dict['ins_api']['outputs']['output']['body']
    except KeyError:
        data = None
    return data


def feature_enabled(device, feature):
    """Checks to see if a feature is enabled

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        feature (str): name nx-os feature

    Returns:
        bool: true if feature enabled, else false

    """
    command = 'show feature'
    check = False

    if feature == 'vn-segment-vlan-based':
        feature = 'vnseg_vlan'
    elif feature == 'telnet':
        feature = 'telnetServer'
    elif feature == 'ssh':
        feature = 'sshServer'
    elif feature == 'hsrp':
        feature = 'hsrp_engine'
    elif feature == 'sftp-server':
        feature = 'sftpServer'
    elif feature == 'scp-server':
        feature = 'scpServer'

    try:
        data = device.show(command)
        data_dict = xmltodict.parse(data[1])
        table = data_dict['ins_api']['outputs']['output']
        error = table.get('clierror', None)
        if error is None:
            features = table['body'].get(
                'TABLE_cfcFeatureCtrlTable')['ROW_cfcFeatureCtrlTable']
        else:
            # For the 3K, the feature table is being returned in the clierror
            # key/taag as unstructured text.  Ugh.
            manual_list = error.split('\n')
            features = {}
            for each in manual_list:
                stripped = each.strip()
                words = stripped.split(' ')
                first = str(words[0])
                last = str(words[-1])
                features[first] = last
            status = features.get(feature, None)
            if status:
                if status.startswith('enabled'):
                    return True
                else:
                    return False
    except (KeyError, AttributeError):
        return check
    if features:
        for each in features:
            feat = str(each['cfcFeatureCtrlName2'])
            if feat == feature:
                enabled = str(each['cfcFeatureCtrlOpStatus2'])
                if enabled.startswith('enabled'):
                    # returning here to not loop through each supported
                    # instance/process of ospf, etc.
                    return True
    return False


def get_commands_to_remove_vpc(domain):
    """Gets commands to remove vpc domain

    Args:
        domain (str): vpc domain ID

    Returns:
        list: ordered list of commands to remove vpc domain

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    commands = []
    commands.append('no vpc domain ' + domain)
    return commands


def peer_link_exists(device):
    """Checks to see if vpc peer link exists

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py

    Returns:
        bool: true if peer link exists, else false

    """
    found = False
    run = get_vpc_running_config(device)
    if run:
        vpc_list = run.split('\n')
        for each in vpc_list:
            if 'peer-link' in each:
                found = True
    return found


def get_hsrp_groups_on_interfaces(device):
    """Gets hsrp groups configured on each interface

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py

    Returns:
        dict: k/v pairs in the form of interface/[group list]

    """
    command = 'show hsrp all'
    xmlReturnData = device.show(command)
    result = xmltodict.parse(xmlReturnData[1])
    hsrp = {}
    try:
        get_data = result['ins_api']['outputs']['output']['body'].get(
            'TABLE_grp_detail')['ROW_grp_detail']
        for entry in get_data:
            interface = str(entry['sh_if_index'].lower())
            value = hsrp.get(interface, 'new')
            if value == 'new':
                hsrp[interface] = []
            group = str(entry['sh_group_num'])
            hsrp[interface].append(group)
    except (KeyError, AttributeError, CLIError):
        hsrp = {}

    return hsrp


def get_hsrp_group(device, group, interface_param):
    """Gets hsrp config for a given interface and group

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        group (str): hsrp group
        interface_param (str): name of interface

    Returns:
        dict: config params for a given hsrp group on a given interface

    """
    command = 'show hsrp group ' + group
    xmlReturnData = device.show(command)
    result = xmltodict.parse(xmlReturnData[1])
    hsrp = []
    try:
        get_data = result['ins_api']['outputs']['output']['body'].get(
            'TABLE_grp_detail')['ROW_grp_detail']
        for hsrp_group in get_data:
            interface = str(hsrp_group['sh_if_index'].lower())
            group = str(hsrp_group['sh_group_num'])
            hsrp_version = str(hsrp_group['sh_group_version'])
            if hsrp_version[-1] == '1':
                version = '1'
            elif hsrp_version[-1] == '2':
                version = '2'
            priority = str(hsrp_group['sh_cfg_prio'])
            preempt = str(hsrp_group['sh_preempt'])
            vip = str(hsrp_group['sh_vip'])
            auth_type = str(hsrp_group.get('sh_authentication_type', None))
            auth_string = str(hsrp_group.get('sh_authentication_data', None))
            # secure = str(get_data.get('sh_keystring_attr','unencrypted'))
            temp = dict(interface=interface, group=group, version=version,
                        priority=priority, preempt=preempt, vip=vip,
                        auth_type=auth_type, auth_string=auth_string)

            hsrp.append(temp)

    except (TypeError, AttributeError, CLIError):
        try:
            interface = str(get_data['sh_if_index'].lower())
            group = str(get_data['sh_group_num'])
            hsrp_version = str(get_data['sh_group_version'])
            if hsrp_version[-1] == '1':
                version = '1'
            elif hsrp_version[-1] == '2':
                version = '2'
            priority = str(get_data['sh_cfg_prio'])
            preempt = str(get_data['sh_preempt'])
            vip = str(get_data['sh_vip'])
            auth_type = str(get_data.get('sh_authentication_type', None))
            auth_string = str(get_data.get('sh_authentication_data', None))
            # secure = str(get_data.get('sh_keystring_attr','unencrypted'))
            temp = dict(interface=interface, group=group, version=version,
                        priority=priority, preempt=preempt, vip=vip,
                        auth_type=auth_type, auth_string=auth_string)
            hsrp.append(temp)
        except:
            hsrp = []

    if hsrp:
        for each in hsrp:
            if interface_param == each['interface']:
                return each
    return {}


def get_commands_remove_hsrp(group, interface):
    """Gets commands to remove an hsrp on an interface

    Args:
        group (str): hsrp group
        interface (str): name of interface

    Returns:
        list: ordered list of commands to remove the hsrp group

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    commands = []
    commands.append('interface ' + interface)
    commands.append('no hsrp ' + group)
    return commands


def get_commands_config_hsrp(delta, interface, args):
    """Gets commands to config hsrp on an interface

    Args:
        delta (set): params to config from nxos_hsrp
        interface (str): name of interface
        args (dict): args sent in from user in nxos_hsrp

    Returns:
        list: ordered list of commands to config hsrp

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    delta = dict(delta)

    CONFIG_ARGS = {
        'group': 'hsrp {group}',
        'priority': 'priority {priority}',
        'preempt': '{preempt}',
        'vip': 'ip {vip}'
    }
    preempt_check = delta.get('preempt', None)
    group = delta.get('group', None)
    if preempt_check:
        if preempt_check == 'enabled':
            delta['preempt'] = 'preempt'
        elif preempt_check == 'disabled':
            delta['preempt'] = 'no preempt'

    commands = []

    for param, value in delta.iteritems():

        command = CONFIG_ARGS.get(param, 'DNE').format(**delta)
        if command and command != 'DNE':
            if param == 'group':
                commands.insert(0, command)
            else:
                commands.append(command)
        command = None

    auth_type = delta.get('auth_type', None)
    auth_string = delta.get('auth_string', None)
    if auth_type or auth_string:
        if not auth_type:
            auth_type = args['auth_type']
        elif not auth_string:
            auth_string = args['auth_string']
        if auth_type == 'md5':
            command = 'authentication md5 key-string ' + auth_string
            commands.append(command)
        elif auth_type == 'text':
            command = 'authentication text ' + auth_string
            commands.append(command)

    if commands and not group:
        commands.insert(0, 'hsrp ' + args['group'])

    version_check = delta.get('version', None)
    if version_check:
        if version_check == '2':
            vcommand = 'hsrp version 2'
        elif version_check == '1':
            vcommand = 'hsrp version 1'
        commands.insert(0, vcommand)
        commands.insert(0, 'interface ' + interface)

    if commands:
        if not commands[0].startswith('interface'):
            commands.insert(0, 'interface ' + interface)

    return commands


def cmd_list_to_string(cmds):
    """Converts list of commands into proper string for NX-API

    Args:
        cmds (list): ordered list of commands

    Returns:
        str: string of commands separated by " ; "

    """
    command = ' ; '.join(cmds)
    return command + ' ;'

def nested_cmd_list_to_string(commands):
    cmds = ''
    if commands:
        cmds = ' '.join(' ; '.join(each) + ' ;'
            for each in commands if each)
    return cmds


def execute_commands(device, commands):
    """Converts a list of lists of commands into semi-colon separated string for use with NX-API
    and exectutes the commands on a given device

    Args:
        commands(list of list(s) of strings): ordered list of list(s) of commands
        device (Device): NX-API-enabled device on which commands are entered

    Returns:
        None

    """
    cmds = nested_cmd_list_to_string(commands)
    if cmds:
        device.config(cmds)

def get_hostname(device, with_domain=False):
    command = 'show hostname'
    xmlReturnData = device.show(command)
    result = xmltodict.parse(xmlReturnData[1])
    hostname = result['ins_api']['outputs']['output']['body']['hostname']

    if not with_domain:
        if '.' in hostname:
            return hostname.split('.')[0]
    return hostname


def get_neighbors(device, neigh_type='cdp'):
    """Gets neighbors from a device

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        neigh_type (str): lldp or cdp

    Returns:
        list: ordered list of dicts (dict per neigh)

    """

    def clean(name):
        if '(' in name and ')' in name:
            return name.split('(')[0]
        else:
            return name

    neighbors = []

    if neigh_type == 'cdp':
        command = 'show cdp neighbors'
        xmlReturnData = device.show(command)
        result = xmltodict.parse(xmlReturnData[1])
        cdp_table = result['ins_api']['outputs']['output']['body'].get(
            'TABLE_cdp_neighbor_brief_info')['ROW_cdp_neighbor_brief_info']
        try:
            for each in cdp_table:
                temp = {}
                local_intf = str(each['intf_id'])
                remote_hostname = clean(str(each['device_id'].split('.')[0]))
                remote_device_type = str(each['platform_id'])
                remote_intf = str(each['port_id'])
                temp = {'platform': remote_device_type,
                        'neighbor': remote_hostname,
                        'neighbor_interface': remote_intf,
                        'local_interface': local_intf}
                neighbors.append(temp)

        except TypeError:
            # only used if there is only one neighbor on a device
            temp = {}
            local_intf = str(cdp_table['intf_id'])
            remote_hostname = str(cdp_table['device_id'].split('.')[0])
            remote_device_type = str(cdp_table['platform_id'])
            remote_intf = str(cdp_table['port_id'])
            temp = {'platform': remote_device_type,
                    'neighbor': remote_hostname,
                    'neighbor_interface': remote_intf,
                    'local_interface': local_intf}
            neighbors.append(temp)

    elif neigh_type == 'lldp':
        command = 'show lldp neighbors'
        xmlReturnData = device.show(command)
        result = xmltodict.parse(xmlReturnData[1])
        lldp_table = result['ins_api']['outputs']['output']['body'].get(
            'TABLE_nbor')['ROW_nbor']
        try:
            for each in lldp_table:
                temp = {}
                local_intf = str(each['l_port_id'])
                remote_hostname = str(each['chassis_id'].split('.')[0])
                remote_intf = str(each['port_id'])
                temp = {'neighbor': remote_hostname,
                        'neighbor_interface': remote_intf,
                        'local_interface': local_intf}
                neighbors.append(temp)

        except TypeError:
            # only used if there is only one neighbor on a device
            temp = {}
            local_intf = str(lldp_table['l_port_id'])
            remote_hostname = str(lldp_table['chassis_id'].split('.')[0])
            remote_intf = str(lldp_table['port_id'])
            temp = {'neighbor': remote_hostname,
                    'neighbor_interface': remote_intf,
                    'local_interface': local_intf}
            neighbors.append(temp)

    return neighbors


def get_facts(device):
    """Gets facts about the network device

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py

    Returns:
        dict: all facts about device

    """
    command = 'show version'
    xml = device.show(command)
    result = xmltodict.parse(xml[1])

    resource_table = result['ins_api']['outputs']['output']['body']
    os = resource_table.get('rr_sys_ver', None)
    kickstart = resource_table.get('kickstart_ver_str', None)
    platform = resource_table.get('chassis_id', None)
    hostname = resource_table.get('host_name', None)
    rr = resource_table.get('rr_reason', None)


    command = 'show interface status'
    try:
        xml = device.show(command)
        result = xmltodict.parse(xml[1])
        resource_table = result['ins_api']['outputs']['output']['body'].get(
            'TABLE_interface')['ROW_interface']
        interface_list = []
        detailed_list = []
        for each in resource_table:
            intf = str(each.get('interface', None))
            if intf:
                temp = {}
                interface_list.append(intf)
                temp['interface'] = intf
                temp['description'] = str(each.get('name', None))
                temp['state'] = str(each.get('state', None))
                temp['vlan'] = str(each.get('vlan', None))
                temp['duplex'] = str(each.get('duplex', None))
                temp['speed'] = str(each.get('speed', None))
                temp['type'] = str(each.get('type', None))
                detailed_list.append(temp)
    except CLIError:
        # added this in to support NXOSv
        detailed_list = []
        interface_list = []

    command = 'show module'
    xml = device.show(command)
    result = xmltodict.parse(xml[1])

    resource_table = result['ins_api']['outputs']['output']['body'].get(
        'TABLE_modinfo')['ROW_modinfo']
    mod_list = []
    try:
        for each in resource_table:
            temp = {}
            temp['ports'] = str(each.get('ports', None))
            temp['type'] = str(each.get('modtype', None))
            temp['model'] = str(each.get('model', None))
            temp['status'] = str(each.get('status', None))
            mod_list.append(temp)
    except (AttributeError, TypeError):
        temp = {}
        temp['ports'] = str(resource_table.get('ports', None))
        temp['type'] = str(resource_table.get('modtype', None))
        temp['model'] = str(resource_table.get('model', None))
        temp['status'] = str(resource_table.get('status', None))
        mod_list.append(temp)

    command = 'show environment'
    xml = device.show(command)
    result = xmltodict.parse(xml[1])

    resource_table = result['ins_api']['outputs']['output']['body']
    power_supply_list = []
    try:
        for each in resource_table['powersup']['TABLE_psinfo']['ROW_psinfo']:
            temp = {}
            temp['number'] = str(each.get('psnum', None))
            temp['model'] = str(each.get('psmodel', None))
            temp['actual_output'] = str(each.get('actual_out', None))
            temp['actual_input'] = str(each.get('actual_in', None))
            temp['total_capacity'] = str(each.get('tot_capa', None))
            temp['status'] = str(each.get('ps_status', None))
            power_supply_list.append(temp)
    except (AttributeError, TypeError):
        temp = {}
        each = resource_table['powersup']['TABLE_psinfo']['ROW_psinfo']
        temp['number'] = str(each.get('psnum', None))
        temp['model'] = str(each.get('psmodel', None))
        temp['actual_output'] = str(each.get('actual_out', None))
        temp['actual_input'] = str(each.get('actual_in', None))
        temp['total_capacity'] = str(each.get('tot_capa', None))
        temp['status'] = str(each.get('ps_status', None))
        power_supply_list.append(temp)

    fan_list = []
    try:
        for each in resource_table['fandetails'].get(
                'TABLE_faninfo')['ROW_faninfo']:
            temp = {}
            temp['name'] = str(each.get('fanname', None))
            temp['model'] = str(each.get('fanmodel', None))
            temp['hw_ver'] = str(each.get('fanhwver', None))
            temp['direction'] = str(each.get('fandir', None))
            temp['status'] = str(each.get('fanstatus', None))
            fan_list.append(temp)
    except (AttributeError, TypeError):
        temp = {}
        each = resource_table['fandetails']['TABLE_faninfo']['ROW_faninfo']
        temp['name'] = str(each.get('fanname', None))
        temp['model'] = str(each.get('fanmodel', None))
        temp['hw_ver'] = str(each.get('fanhwver', None))
        temp['direction'] = str(each.get('fandir', None))
        temp['status'] = str(each.get('fanstatus', None))
        fan_list.append(temp)

    facts = dict(
        os=os,
        kickstart_image=kickstart,
        platform=platform,
        hostname=hostname,
        last_reboot_reason=rr,
        interfaces=interface_list,
        interfaces_detail=detailed_list,
        modules=mod_list,
        power_supply_info=power_supply_list,
        fan_info=fan_list,
        vlan_list=get_vlan_info(device)
    )

    return facts


def get_interface_detail(device, interface):
    """Gets  stats for specified interface

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        interface (str): full name of interface

    Returns:
        dict: all params from show interface command

    """
    command = 'show interface ' + interface
    try:
        xml = device.show(command)
    except CLIError:
        return {}

    result = xmltodict.parse(xml[1])
    each = result['ins_api']['outputs']['output']['body'].get(
        'TABLE_interface')['ROW_interface']
    intf = str(each.get('interface', None))
    if intf:
        temp = {}
        temp['interface'] = intf
        temp['state'] = str(each.get('state', None))
        temp['admin_state'] = str(each.get('admin_state', None))
        temp['share_state'] = str(each.get('share_state', None))
        temp['hw_desc'] = str(each.get('eth_hw_desc', None))
        temp['hw_addr'] = str(each.get('eth_hw_addr', None))
        temp['bia_addr'] = str(each.get('eth_bia_addr', None))
        temp['description'] = str(each.get('description', None))
        temp['mtu'] = str(each.get('eth_mtu', None))
        temp['bw'] = str(each.get('bw', None))
        temp['delay'] = str(each.get('dly', None))
        temp['reliability'] = str(each.get('reliability', None))
        temp['tx_load'] = str(each.get('eth_txload', None))
        temp['rx_load'] = str(each.get('rx_txload', None))
        temp['medium'] = str(each.get('medium', None))
        temp['mode'] = str(each.get('eth_mode', None))
        temp['duplex'] = str(each.get('eth_duplex', None))
        temp['speed'] = str(each.get('eth_speed', None))
        temp['media'] = str(each.get('eth_media', None))
        temp['autoneg'] = str(each.get('eth_autoneg', None))
        temp['description'] = str(each.get('description', None))
        temp['mtu'] = str(each.get('eth_mtu', None))
        temp['bw'] = str(each.get('bw', None))
        temp['delay'] = str(each.get('dly', None))
        temp['reliability'] = str(each.get('reliability', None))
        temp['tx_load'] = str(each.get('eth_txload', None))
        temp['rx_load'] = str(each.get('rx_txload', None))
        temp['in_flowctrl'] = str(each.get('eth_in_flowctrl', None))
        temp['out_flowctrl'] = str(each.get('eth_out_flowctrl', None))
        temp['mdix'] = str(each.get('eth_mdix', None))
        temp['ratemode'] = str(each.get('eth_ratemode', None))
        temp['swt_monitor'] = str(each.get('eth_swt_monitor', None))
        temp['ethertype'] = str(each.get('eth_ethertype', None))
        temp['eee_state'] = str(each.get('eth_eee_state', None))
        temp['link_flapped'] = str(each.get('eth_link_flapped', None))
        temp['clear_counters'] = str(each.get('eth_clear_counters', None))
        temp['reset_cntr'] = str(each.get('eth_reset_cntr', None))
        temp['load_interval1_rx'] = str(each.get(
            'eth_load_interval1_rx', None))
        temp['inrate1_bits'] = str(each.get('eth_inrate1_bits', None))
        temp['inrate1_pkts'] = str(each.get('eth_inrate1_pkts', None))
        temp['load_interval1_tx'] = str(each.get(
            'eth_load_interval1_tx', None))
        temp['outrate1_bits'] = str(each.get('eth_outrate1_bits', None))
        temp['outrate1_pkts'] = str(each.get('eth_outrate1_pkts', None))
        temp['inucast'] = str(each.get('eth_inucast', None))
        temp['inmcast'] = str(each.get('eth_inmcast', None))
        temp['inbcast'] = str(each.get('eth_inbcast', None))
        temp['inpkts'] = str(each.get('eth_inpkts', None))
        temp['inbytes'] = str(each.get('eth_inbytes', None))
        temp['jumbo_inpkts'] = str(each.get('eth_jumbo_inpkts', None))
        temp['storm_supp'] = str(each.get('eth_storm_supp', None))
        temp['runts'] = str(each.get('eth_runts', None))
        temp['giants'] = str(each.get('eth_giants', None))
        temp['crc'] = str(each.get('eth_crc', None))
        temp['nobuf'] = str(each.get('eth_nobuf', None))
        temp['inerr'] = str(each.get('eth_inerr', None))
        temp['frame'] = str(each.get('eth_frame', None))
        temp['overrun'] = str(each.get('eth_overrun', None))
        temp['underrun'] = str(each.get('eth_underrun', None))
        temp['ignored'] = str(each.get('eth_ignored', None))
        temp['watchdog'] = str(each.get('eth_watchdog', None))
        temp['bad_eth'] = str(each.get('eth_bad_eth', None))
        temp['bad_proto'] = str(each.get('eth_bad_proto', None))
        temp['in_ifdown_drops'] = str(each.get('eth_in_ifdown_drops', None))
        temp['dribble'] = str(each.get('eth_dribble', None))
        temp['indiscard'] = str(each.get('eth_indiscard', None))
        temp['inpause'] = str(each.get('eth_inpause', None))
        temp['outucast'] = str(each.get('eth_outucast', None))
        temp['outmcast'] = str(each.get('eth_outmcast', None))
        temp['outbcast'] = str(each.get('eth_outbcast', None))
        temp['outpkts'] = str(each.get('eth_outpkts', None))
        temp['outbytes'] = str(each.get('eth_outbytes', None))
        temp['jumbo_outpkts'] = str(each.get('eth_jumbo_outpkts', None))
        temp['outerr'] = str(each.get('eth_outerr', None))
        temp['coll'] = str(each.get('eth_coll', None))
        temp['deferred'] = str(each.get('eth_deferred', None))
        temp['latecoll'] = str(each.get('eth_latecoll', None))
        temp['lostcarrier'] = str(each.get('eth_lostcarrier', None))
        temp['nocarrier'] = str(each.get('eth_nocarrier', None))
        temp['babbles'] = str(each.get('eth_babbles', None))
        temp['outdiscard'] = str(each.get('eth_outdiscard', None))
        temp['outpause'] = str(each.get('eth_outpause', None))
        return temp
    return {}


def get_udld_global(device):
    """Gets  udld global config

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py

    Returns:
        dict: global udld params

    """
    command = 'show udld global'
    xmldata = device.show(command)
    result = xmltodict.parse(xmldata[1])

    resource_table = result['ins_api']['outputs']['output']['body']

    # status returned will be 'enabled' or 'aggressive-enabled'
    status = str(resource_table.get('udld-global-mode', None))
    if status == 'enabled-aggressive':
        aggressive = 'enabled'
    else:
        aggressive = 'disabled'

    interval = str(resource_table.get('message-interval', None))

    udld = dict(udld_global=status, msg_time=interval, aggressive=aggressive)

    return udld


def is_interface_copper(device, interface):
    """Checks to see if interface is copper

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        interface (str): Full name of the interface

    Returns:
        bool: True if interface is copper, else false

    """
    command = 'show interface status'
    copper = []
    try:
        data = device.show(command)
        data_dict = xmltodict.parse(data[1])
        table = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_interface')['ROW_interface']
        for each in table:
            itype = each.get('type', 'DNE')
            if 'CU' in itype or '1000' in itype or '10GBaseT' in itype:
                copper.append(str(each['interface'].lower()))
    except (KeyError, AttributeError):
        pass
    # 'ethernet' is used in comaparision.  FULL NAME is required
    # from calling module
    if interface in copper:
        found = True
    else:
        found = False

    return found


def get_udld_interface(device, interface):
    """Get udld interface config

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        interface (str): Full name of the interface

    Returns:
        dict: single k/v pair for udld mode of interface

    """
    command = 'show udld ' + interface
    interface_udld = {}
    mode = None
    try:
        data = device.show(command)
        data_dict = xmltodict.parse(data[1])
        table = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_interface')['ROW_interface']

        # will return enabled, disabled, or enabled-aggressive
        status = str(table.get('mib-port-status', None))
        agg = str(table.get('mib-aggresive-mode', 'disabled'))

        if agg == 'enabled':
            mode = 'aggressive'
        else:
            mode = status

        interface_udld['mode'] = mode

    # fix except for more granular exceptions
    except (KeyError, AttributeError, CLIError):
        interface_udld = {}

    return interface_udld


def get_commands_config_udld_interface(delta, interface, device, existing):
    """Gets commands to config udld on an interface

    Args:
        delta (dict): params to config- from nxos_udld_interface
        interface (str): Full name of the interface
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        existing (dict): params of existing config- from nxos_udld_interface

    Returns:
        list: ordered list of commands to config udld interface

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    commands = []
    copper = is_interface_copper(device, interface)
    if delta:
        mode = delta['mode']
        if mode == 'aggressive':
            command = 'udld aggressive'
        elif copper:
            if mode == 'enabled':
                if existing['mode'] == 'aggressive':
                    command = 'no udld aggressive ; udld enable'
                else:
                    command = 'udld enable'
            elif mode == 'disabled':
                command = 'no udld enable'
        elif not copper:
            if mode == 'enabled':
                if existing['mode'] == 'aggressive':
                    command = 'no udld aggressive ; no udld disable'
                else:
                    command = 'no udld disable'
            elif mode == 'disabled':
                command = 'udld disable'
    if command:
        commands.append(command)
        commands.insert(0, 'interface ' + interface)

    return commands


def get_commands_remove_udld_interface(delta, interface, device, existing):
    """Gets commands to remove udld config on an interface

    Args:
        delta (dict): params to config- from nxos_udld_interface
        interface (str): Full name of the interface
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        existing (dict): params of existing config- from nxos_udld_interface

    Returns:
        list: ordered list of commands to remove config for udld

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    commands = []
    copper = is_interface_copper(device, interface)

    if delta:
        mode = delta['mode']
        if mode == 'aggressive':
            command = 'no udld aggressive'
        elif copper:
            if mode == 'enabled':
                command = 'no udld enable'
            elif mode == 'disabled':
                command = 'udld enable'
        elif not copper:
            if mode == 'enabled':
                command = 'udld disable'
            elif mode == 'disabled':
                command = 'no udld disable'
    if command:
        commands.append(command)
        commands.insert(0, 'interface ' + interface)

    return commands


def get_commands_config_udld_global(delta):
    """Gets commands to config udld global config

    Args:
        delta (dict): params to config- from nxos_udld

    Returns:
        list: ordered list of commands to config udld

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    CONFIG_ARGS = {
        'enabled': 'udld aggressive',
        'disabled': 'no udld aggressive',
        'msg_time': 'udld message-time {msg_time}',
        'reset': 'udld reset'
    }
    commands = []
    for param, value in delta.iteritems():
        if param == 'aggressive':
            if value == 'enabled':
                command = 'udld aggressive'
            elif value == 'disabled':
                command = 'no udld aggressive'
        else:
            command = CONFIG_ARGS.get(param, 'DNE').format(**delta)
        if command and command != 'DNE':
            commands.append(command)
        command = None
    return commands


def get_commands_remove_udld_global(delta):
    """Gets commands to remove udld global config

    Args:
        delta (dict): params to config- from nxos_udld

    Returns:
        list: ordered list of commands to remove udld config

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    CONFIG_ARGS = {
        'aggressive': 'no udld aggressive',
        'msg_time': 'no udld message-time {msg_time}',
    }
    commands = []
    for param, value in delta.iteritems():
        command = CONFIG_ARGS.get(param, 'DNE').format(**delta)
        if command and command != 'DNE':
            commands.append(command)
        command = None
    return commands


def get_mtu(device, interface):
    """Gets mtu config for device and/or interface

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        interface (str): Full name of the interface

    Returns:
        dict: k/v pairs for interface mtu and system mtu

    """
    command = 'show interface ' + interface
    resource = {}
    intf_dict = {}
    try:
        data = device.show(command)
        data_dict = xmltodict.parse(data[1])
        intf_dict = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_interface')['ROW_interface']
    except (KeyError, AttributeError, CLIError):
        resource = {}

    if intf_dict:
        resource['mtu'] = str(
            intf_dict.get('eth_mtu',
                          intf_dict.get('svi_mtu', 'unreadable_via_api')))
        resource['sysmtu'] = get_system_mtu(device)['sysmtu']

    return resource


def get_system_mtu(device):
    """Gets system mtu value

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
    Returns:
      dict: single k/v pair for system mtu

    """
    command = 'show run all | inc jumbomtu'
    mtu = None
    data = device.show(command, text=True)
    data_dict = xmltodict.parse(data[1])
    ml_data = data_dict['ins_api']['outputs']['output']['body']
    mtu = str(ml_data.split(' ')[-1])

    return dict(sysmtu=mtu)


def get_commands_config_mtu(delta, interface):
    """Gets commands to config mtu

    Args:
        delta (dict): params to config- from nxos_mtu
        interface (str): Full name of the interface

    Returns:
        list: ordered list of commands to config mtu

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    CONFIG_ARGS = {
        'mtu': 'mtu {mtu}',
        'sysmtu': 'system jumbomtu {sysmtu}',
    }

    commands = []
    for param, value in delta.iteritems():
        command = CONFIG_ARGS.get(param, 'DNE').format(**delta)
        if command and command != 'DNE':
            commands.append(command)
        command = None
    mtu_check = delta.get('mtu', None)
    if mtu_check:
        commands.insert(0, 'interface ' + interface)
    return commands


def get_commands_remove_mtu(delta, interface):
    """Gets commands to remove mtu config

    Args:
        delta (dict): params to config- from nxos_mtu
        interface (str): Full name of the interface

    Returns:
        list: ordered list of commands to remove mtu config

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    CONFIG_ARGS = {
        'mtu': 'no mtu {mtu}',
        'sysmtu': 'no system jumbomtu {sysmtu}',
    }
    commands = []
    for param, value in delta.iteritems():
        command = CONFIG_ARGS.get(param, 'DNE').format(**delta)
        if command and command != 'DNE':
            commands.append(command)
        command = None
    mtu_check = delta.get('mtu', None)
    if mtu_check:
        commands.insert(0, 'interface ' + interface)
    return commands


def get_feature_list(device):
    """Gets features supported on switch

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py

    Returns:
        list: feature list

    """
    feature_set = set()
    features = None
    feature_list = None
    command = 'show feature'
    try:
        data = device.show(command)
        data_dict = xmltodict.parse(data[1])
        features = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_cfcFeatureCtrlTable')['ROW_cfcFeatureCtrlTable']
    except (KeyError, AttributeError):
        raw_list = data_dict['ins_api']['outputs']['output']['clierror'].split('\n')
        features = []
        for line in raw_list[2:]:
            tmp = {}
            split_line = line.split(' ')
            feat = split_line[0].strip()
            print feat
            tmp['cfcFeatureCtrlName2'] = feat
            features.append(tmp)
    except:
        return []

    if features:
        for each in features:
            feature = str(each['cfcFeatureCtrlName2'])
            if feature == 'vnseg_vlan':
                feature = 'vn-segment-vlan-based'
            elif feature == 'telnetServer':
                feature = 'telnet'
            elif feature == 'sshServer':
                feature = 'ssh'
            elif feature == 'hsrp_engine':
                feature = 'hsrp'
            elif feature == 'sftpServer':
                feature = 'sftp-server'
            elif feature == 'scpServer':
                feature = 'scp-server'
            elif feature in ['bfd_app', 'tunnel', 'onep']:
                feature = None
            if feature:
                feature_set.update([feature])

    feature_list = list(feature_set)

    return feature_list


def get_commands_enable_feature(feature):
    """Get commands to enable feature

    Args:
        feature (str): name of feature to enable

    Returns:
        list: ordered list commands to enable feature

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    commands = []
    if feature:
        command = 'feature ' + feature
        commands.append(command)
    return commands


def get_commands_disable_feature(feature):
    """Get commands to disable feature

    Args:
        feature (str): name of feature to disable

    Returns:
        list: ordered list commands to disable feature

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    commands = []
    if feature:
        command = 'no feature ' + feature
        commands.append(command)
    return commands


def switch_files_list(device, path='bootflash:'):
    """Get list of files/dirs within a specific a directory

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        path (str): path of a dir on switch

    Returns:
        list: list of files or sub-dirs in a given directory
        [], if invalid path

    """
    command = 'dir ' + path
    try:
        data = device.show(command, text=True)
        data_dict = xmltodict.parse(data[1])
        files = data_dict['ins_api']['outputs']['output']['body']
    except (KeyError, CLIError):
        return []
    file_list = files.split('\n')
    my_files = []
    for each in file_list[:-5]:
        my_file = each.split(' ')[-1]
        my_files.append(str(my_file))
    return my_files


def get_file_path(local_path):
    """Get file and dir given a full path
      Note: only to be used internally right now

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        path (str): path of a dir on switch

    Returns:
        list: list of files or sub-dirs in a given directory
        [], if invalid path

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    location = local_path.split(':')[0]
    rightmost = local_path.split(':')[-1]
    if '/' in rightmost:
        file_name = rightmost.split('/')[-1]
        path_list = rightmost.split('/')[:-1]
        path = location + ':' + '/'.join(path_list) + '/'
    else:
        file_name = rightmost
        path = location + ':'
    return file_name, path


def full_dir_check(device, path):
    """Checks to see if directory exists

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        path (str): path of a dir on switch

    Returns:
        bool: true if exists, else false

    Note:
        Specific for Ansible module(s).  Not to be called otherwise.

    """
    filename, path = get_file_path(path)
    path_list = path.split(':')
    preamble = path_list[0] + ':'
    rpath = path_list[1]
    dir_list = []
    if '/' in rpath:
        rpath_list = rpath.split('/')
        for each in rpath_list:
            if each:
                dir_list.append(each)

    active_dir_file_list = switch_files_list(device, preamble)
    bpath = ''
    valid = True, None
    for each in dir_list:
        bpath = bpath + each + '/'
        if each + '/' in active_dir_file_list:
            command = '{0}{1}'.format(preamble, bpath)
            active_dir_file_list = switch_files_list(device, command)
        else:
            valid = False, each + '/'

    return valid


def create_dir(device, path):
    """Creates dir on the switch

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        path (str): path of a dir on switch

    Returns:
        bool: true if it's created, else false if it already exists

    """
    command = 'mkdir ' + path
    try:
        data = device.show(command, text=True)
        data_dict = xmltodict.parse(data[1])
        check = data_dict['ins_api']['outputs']['output']

        # if clierror exists, unfortunately it is returning
        # None (as NOT shown in the sandbox)
        # using this the opposite how it should be used
        clierror = check.get('clierror', 'NOERROR')
    except (KeyError, AttributeError, CLIError):
        return False

    if not clierror:
        return False
    elif clierror == 'NOERROR':
        return True


def delete_dir(device, path):
    """Deletes dir on the switch

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        path (str): path of a dir on switch

    Returns:
        bool: true if it's deleted, else false if it doesn't exist

    """
    term = 'terminal dont-ask ; '
    command = term + 'delete ' + path
    try:
        data = device.show(command, text=True)
        data_dict = xmltodict.parse(data[1])

        # second element b/c the 'delete' is the second command
        check = data_dict['ins_api']['outputs']['output'][1]
        # if clierror exists, unfortunately it is returning
        # None (as NOT shown in the sandbox)
        # using this the opposite how it should be used
        clierror = check.get('clierror', 'NOERROR')
    except (KeyError, AttributeError, CLIError):
        return False

    if not clierror:
        return False
    elif clierror == 'NOERROR':
        return True
