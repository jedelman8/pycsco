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

from pycsco.nxos.utils import legacy
from pycsco.nxos.error import CLIError

try:
    import xmltodict
except ImportError as e:
    print '*' * 30
    print e
    print '*' * 30

__all__ = ['get_igmp_defaults', 'get_igmp_global', 'get_igmp_snooping',
           'get_igmp_snooping_defaults', 'get_igmp_interface',
           'get_pim_interface_defaults', 'get_pim_interface',
           'get_igmp_interface_defaults']


def get_igmp_defaults():
    """Retrieves IGMP default configuration parameters

    Returns:
        Dictionary

    """
    flush_routes = False
    enforce_rtr_alert = False

    args = dict(flush_routes=flush_routes,
                enforce_rtr_alert=enforce_rtr_alert)

    default = dict((param, value) for (param, value) in args.iteritems()
                   if value is not None)

    return default


def config_igmp(delta):
    """Generates command list to configure IGMP mainly for Ansible modules

    Args:
        delta (dict): key/values of IGMP settings to configure

    Returns:
        List
    """

    CMDS = {
        'flush_routes': 'ip igmp flush-routes',
        'enforce_rtr_alert': 'ip igmp enforce-router-alert'
    }
    commands = []
    for key, value in delta.iteritems():
        if value:
            command = CMDS.get(key)
        else:
            command = 'no ' + CMDS.get(key)
        if command:
            commands.append(command)
        command = None

    return commands


def get_igmp_global(device):
    """Retrieves igmp global configurations

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class from pycsco

    Returns:
        Dictionary
    """
    command = 'show run igmp'
    data = device.show(command, text=True)
    data_dict = xmltodict.parse(data[1])

    raw_text = data_dict['ins_api']['outputs']['output']['body']

    existing = legacy.get_structured_data('igmp_global.tmpl', raw_text)

    flush = False
    enforce = False
    for each in existing:
        value = each.get('igmp')
        if 'flush' in value:
            flush = True
        elif 'enforce' in value:
            enforce = True

    existing = dict(flush_routes=flush, enforce_rtr_alert=enforce)

    return existing


def get_igmp_snooping(device):
    """Retrieves igmp snooping configurations

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class from pycsco

    Returns:
        Dictionary
    """

    command = 'show ip igmp snooping'
    data = device.show(command, text=True)
    data_dict = xmltodict.parse(data[1])
    raw_text = data_dict['ins_api']['outputs']['output']['body']

    # existing returns a list of dictionaries
    existing = legacy.get_structured_data('igmp_snooping.tmpl', raw_text)[0]
    if not existing.get('proxy'):
        existing['proxy'] = '5'
    # TODO need to add PROXY BACK INT CONFIG MODULES and ANSIBLE MOD

    command = 'show run all | inc snooping'
    data = device.show(command, text=True)
    data_dict = xmltodict.parse(data[1])
    raw_text = data_dict['ins_api']['outputs']['output']['body']

    command = 'show ip igmp snooping'
    data = device.show(command)
    data_dict = xmltodict.parse(data[1])

    try:
        my_data = data_dict['ins_api']['outputs']['output']['body']

        enabled = my_data.get('enabled')
        link_local_grp_supp = my_data.get('glinklocalgrpsup')
        v3_report_supp = my_data.get('gv3repsup')
        # E Raised this: Enable v3-report-suppression on vlan to take effect...
        # with this command: ip igmp snooping v3-report-suppression
        report_supp = my_data.get('grepsup')
        existing2 = dict(snooping=enabled,
                         link_local_grp_supp=link_local_grp_supp,
                         report_supp=report_supp,
                         v3_report_supp=v3_report_supp)
    except (KeyError, AttributeError):
        existing2 = {}
        # need to fix this

    existing2.update(existing)

    for k, v in existing2.iteritems():
        if v in ['true', 'enabled']:
            existing2[k] = True
        elif v in ['false', 'disabled']:
            existing2[k] = False

    return existing2


def get_igmp_snooping_defaults():
    """Retrieves igmp snooping default configurations

    Returns:
        Dictionary
    """

    group_timeout = 'dummy'
    report_supp = True
    link_local_grp_supp = True
    v3_report_supp = False
    snooping = True
    optimize_mcast_flood = True

    args = dict(snooping=snooping, link_local_grp_supp=link_local_grp_supp,
                optimize_mcast_flood=optimize_mcast_flood,
                report_supp=report_supp, v3_report_supp=v3_report_supp,
                group_timeout=group_timeout)

    default = dict((param, value) for (param, value) in args.iteritems()
                   if value is not None)

    return default


def config_igmp_snooping(delta, existing, default=False):
    """Generates command list to configure IGMP  snooping for Ansible modules

    Args:
        delta (dict): key/values of IGMP snooping settings to configure

    Returns:
        List
    """
    CMDS = {
        'snooping': 'ip igmp snooping',
        'group_timeout': 'ip igmp snooping group-timeout {}',
        'link_local_grp_supp': 'ip igmp snooping link-local-groups-suppression',
        'optimize_mcast_flood': 'ip igmp snooping optimise-multicast-flood',
        'v3_report_supp': 'ip igmp snooping v3-report-suppression',
        'report_supp': 'ip igmp snooping report-suppression'
    }

    commands = []
    command = None
    for k, v in delta.iteritems():
        if v:
            # this next check is funky & used when defaulting the group timeout
            # funky because there is technically no default, so we just need to
            # use the 'no' command, but with the current value set!
            # dummy is also set to always ensure group_timeout is in delta when
            # defaulting the config
            if default and k == 'group_timeout':
                if existing.get(k):
                    command = 'no ' + CMDS.get(k).format(existing.get(k))
            else:
                command = CMDS.get(k).format(v)
        else:
            command = 'no ' + CMDS.get(k).format(v)

        if command:
            commands.append(command)
        command = None

    return commands


def get_igmp_interface(device, interface):
    """Retrieves IGMP interface config params for a given interface

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        interface (str): full name of the interface

    Returns:
        Dictionary

    """
    command = 'show ip igmp interface ' + interface

    try:
        data = device.show(command)
        data_dict = xmltodict.parse(data[1])
        igmp = {}
    except CLIError:
        return {}

    try:
        resource = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_vrf')['ROW_vrf']['TABLE_if']['ROW_if']
        igmp['version'] = str(resource['IGMPVersion'])
        igmp['startup_query_interval'] = str(
            resource['ConfiguredStartupQueryInterval']
            )
        igmp['startup_query_count'] = str(resource['StartupQueryCount'])
        igmp['robustness'] = str(resource['RobustnessVariable'])
        igmp['querier_timeout'] = str(resource['QuerierTimeout'])
        igmp['query_mrt'] = str(resource['ConfiguredMaxResponseTime'])
        igmp['query_interval'] = str(resource['ConfiguredQueryInterval'])
        igmp['last_member_qrt'] = str(resource['LastMemberMTR'])
        igmp['last_member_query_count'] = str(resource['LastMemberQueryCount'])
        igmp['group_timeout'] = str(resource['ConfiguredGroupTimeout'])
        report_llg = str(resource['ReportingForLinkLocal'])
        if report_llg == 'true':
            igmp['report_llg'] = True
        elif report_llg == 'false':
            igmp['report_llg'] = False
        igmp['group_timeout'] = str(resource['ConfiguredGroupTimeout'])
        immediate_leave = str(resource['ImmediateLeave'])  # returns en or dis
        if immediate_leave == 'en':
            igmp['immediate_leave'] = True
        elif immediate_leave == 'dis':
            igmp['immediate_leave'] = False

    except (KeyError, AttributeError):
        pass

    # the  next block of code is used to retrieve anything with:
    # ip igmp static-oif *** i.e.. could be route-map ROUTEMAP
    # or PREFIX source <ip>, etc.
    command = 'show run interface {0} | inc oif'.format(interface)
    data = device.show(command, text=True)

    data_dict = xmltodict.parse(data[1])

    raw_text = data_dict['ins_api']['outputs']['output']['body']

    # existing returns a list of dictionaries
    staticoif = legacy.get_structured_data('igmp_static_oif.tmpl', raw_text)
    # staticoif returns a list of dicts

    new_staticoif = []
    temp = {}
    for counter, data in enumerate(staticoif):
        for k, v in data.iteritems():
            if v:
                temp[k] = v
        if temp:
            new_staticoif.append(temp)
        temp = {}

    igmp['oif_routemap'] = None
    igmp['oif_prefix_source'] = []
    if new_staticoif:
        if len(new_staticoif) == 1 and new_staticoif[0].get('routemap'):
            igmp['oif_routemap'] = new_staticoif[0]['routemap']
        else:
            igmp['oif_prefix_source'] = new_staticoif

    return igmp


def config_igmp_interface(delta, found_both, found_prefix):
    """Generates command list to configure IGMP interface settings
       for Ansible modules

    Args:
        delta (dict): key/values of IGMP snooping settings to configure

    Returns:
        List
    """

    CMDS = {
        'version': 'ip igmp version {0}',
        'startup_query_interval': 'ip igmp startup-query-interval {0}',
        'startup_query_count': 'ip igmp startup-query-count {0}',
        'robustness': 'ip igmp robustness-variable {0}',
        'querier_timeout': 'ip igmp querier-timeout {0}',
        'query_mrt': 'ip igmp query-max-response-time {0}',
        'query_interval': 'ip igmp query-interval {0}',
        'last_member_qrt': 'ip igmp last-member-query-response-time {0}',
        'last_member_query_count': 'ip igmp last-member-query-count {0}',
        'group_timeout': 'ip igmp group-timeout {0}',
        'report_llg': 'ip igmp report-link-local-groups',
        'immediate_leave': 'ip igmp immediate-leave',
        'oif_prefix_source': 'ip igmp static-oif {0} source {1} ',
        'oif_routemap': 'ip igmp static-oif route-map {0}',
        'oif_prefix': 'ip igmp static-oif {0}',
    }

    commands = []
    command = None

    for k, v in delta.iteritems():
        if k in ['source', 'oif_source'] or found_both or found_prefix:
            pass
        elif k == 'prefix':
            if delta.get('source'):
                command = CMDS.get('oif_prefix_source').format(
                    delta.get('prefix'), delta.get('source')
                    )
            else:
                command = CMDS.get('oif_prefix').format(delta.get('prefix'))
        elif k == 'oif_prefix':
            if delta.get('oif_source'):
                command = CMDS.get('oif_prefix_source').format(
                    delta.get('oif_prefix'),
                    delta.get('oif_source')
                    )
            else:
                command = CMDS.get('oif_prefix').format(
                    delta.get('oif_prefix')
                    )
        elif v:
            command = CMDS.get(k).format(v)
        elif not v:
            command = 'no ' + CMDS.get(k).format(v)

        if command:
            commands.append(command)
        command = None

    return commands


def config_default_igmp_interface(existing, delta, found_both, found_prefix):

    commands = []
    proposed = get_igmp_interface_defaults()
    delta = dict(set(proposed.iteritems()).difference(existing.iteritems()))
    if delta:
        command = config_igmp_interface(delta, found_both, found_prefix)

        if command:
            for each in command:
                commands.append(each)

    return commands


def get_igmp_interface_defaults():
    """Generates command list that will be used to default interface
       configs used for IGMP

    Returns:
        List
    """
    version = '2'
    startup_query_interval = '31'
    startup_query_count = '2'
    robustness = '2'
    querier_timeout = '255'
    query_mrt = '10'
    query_interval = '125'
    last_member_qrt = '1'
    last_member_query_count = '2'
    group_timeout = '260'
    report_llg = False
    immediate_leave = False

    args = dict(version=version, startup_query_interval=startup_query_interval,
                startup_query_count=startup_query_count, robustness=robustness,
                querier_timeout=querier_timeout, query_mrt=query_mrt,
                query_interval=query_interval, last_member_qrt=last_member_qrt,
                last_member_query_count=last_member_query_count,
                group_timeout=group_timeout, report_llg=report_llg,
                immediate_leave=immediate_leave)

    default = dict((param, value) for (param, value) in args.iteritems()
                   if value is not None)

    return default


def config_remove_oif(existing, existing_oif_prefix_source):
    """Generates command list to remove a static-oif configuration
       for an Ansible module

    Args:
        oif_prefix (str): IP multicast prefix
        oif_source (str): IP source
        oif_routemap (str): name of routemap to use for filtering
        found_both: (bool): Flag from ansible mod stating if a prefix
                            and source are changing
        found_prefix: (bool): Flag from ansible mod stating if only
                              a prefix is changing

    Returns:
        List
    """

    commands = []
    command = None
    if existing.get('routemap'):
        command = 'no ip igmp static-oif route-map {0}'.format(
                                                    existing.get('routemap'))
    if existing_oif_prefix_source:
        for each in existing_oif_prefix_source:
            if each.get('prefix') and each.get('source'):
                command = 'no ip igmp static-oif {0} source {1} '.format(
                    each.get('prefix'), each.get('source')
                    )
            elif each.get('prefix'):
                command = 'no ip igmp static-oif {0}'.format(
                    each.get('prefix')
                    )
            if command:
                commands.append(command)
            command = None

    return commands


def get_pim_interface(device, interface):
    """Gets pim config for a given interface

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        interface (str): Full interface name

    Returns:
        Dictionary

    """
    command = 'show ip pim interface ' + interface
    try:
        xmlReturnData = device.show(command)
    except CLIError:
        return {}

    result = xmltodict.parse(xmlReturnData[1])
    pim_interface = {}

    try:
        get_data = result['ins_api']['outputs']['output']['body'].get(
            'TABLE_iod')['ROW_iod']

        if isinstance(get_data.get('dr-priority'), unicode) or \
                isinstance(get_data.get('dr-priority'), str):
            pim_interface['dr_prio'] = get_data.get('dr-priority')
        else:
            pim_interface['dr_prio'] = get_data.get('dr-priority')[0]

        pim_interface['hello_interval'] = get_data.get('hello-interval-sec')
        border = get_data.get('is-border')

        if border == 'true':
            pim_interface['border'] = True
        elif border == 'false':
            pim_interface['border'] = False

        isauth = get_data.get('isauth-config')
        if isauth == 'true':
            pim_interface['isauth'] = True
        elif isauth == 'false':
            pim_interface['isauth'] = False

        pim_interface['neighbor_policy'] = get_data.get('nbr-policy-name')
        if pim_interface['neighbor_policy'] == 'none configured':
            pim_interface['neighbor_policy'] = None

        jp_in_policy = get_data.get('jp-in-policy-name')
        pim_interface['jp_policy_in'] = jp_in_policy
        if jp_in_policy == 'none configured':
            pim_interface['jp_policy_in'] = None

        if isinstance(get_data.get('jp-out-policy-name'), unicode) or \
                isinstance(get_data.get('jp-out-policy-name'), str):
            pim_interface['jp_policy_out'] = get_data.get('jp-out-policy-name')
        else:
            pim_interface['jp_policy_out'] = get_data.get(
                'jp-out-policy-name')[0]

        if pim_interface['jp_policy_out'] == 'none configured':
            pim_interface['jp_policy_out'] = None

    except (KeyError, AttributeError):
        return {}

    command = 'show run interface ' + interface
    xmlReturnData = device.show(command, text=True)
    result = xmltodict.parse(xmlReturnData[1])

    get_data = result['ins_api']['outputs']['output']['body']
    all_lines = get_data.split('\n')
    jp_configs = []
    neigh = None
    for each in all_lines:
        if 'jp-policy' in each:
            jp_configs.append(str(each.strip()))
        elif 'neighbor-policy' in each:
            neigh = str(each)

    pim_interface['neighbor_type'] = None
    neigh_type = None
    if neigh:
        if 'prefix-list' in neigh:
            neigh_type = 'prefix'
        else:
            neigh_type = 'routemap'
    pim_interface['neighbor_type'] = neigh_type

    len_existing = len(jp_configs)
    list_of_prefix_type = len([x for x in jp_configs if 'prefix-list' in x])
    jp_type_in = None
    jp_type_out = None
    jp_bidir = False
    if len_existing == 1:
        # determine type
        last_word = jp_configs[0].split(' ')[-1]
        if last_word == 'in':
            if list_of_prefix_type:
                jp_type_in = 'prefix'
            else:
                jp_type_in = 'routemap'
        elif last_word == 'out':
            if list_of_prefix_type:
                jp_type_out = 'prefix'
            else:
                jp_type_out = 'routemap'
        else:
            jp_bidir = True
            if list_of_prefix_type:
                jp_type_in = 'prefix'
                jp_type_out = 'routemap'
            else:
                jp_type_in = 'routemap'
                jp_type_out = 'routemap'
    else:
        for each in jp_configs:
            last_word = each.split(' ')[-1]
            if last_word == 'in':
                if 'prefix-list' in each:
                    jp_type_in = 'prefix'
                else:
                    jp_type_in = 'routemap'
            elif last_word == 'out':
                if 'prefix-list' in each:
                    jp_type_out = 'prefix'
                else:
                    jp_type_out = 'routemap'

    pim_interface['jp_type_in'] = jp_type_in
    pim_interface['jp_type_out'] = jp_type_out
    pim_interface['jp_bidir'] = jp_bidir

    return pim_interface


def config_pim_interface(delta, existing, jp_bidir, isauth):
    """Generates command list to configure PIM on an interface within an
       Ansible module

    Args:
        delta (dict): k/v pairs to configure PIM on an interface
        existing (dict): k/v pairs of existing configuration on the interface
        jp_bidir (bool): flag to see if join-prune policy already exists
                         on the interface with a single command (not in/out)

    Returns:
        List

    """

    command = None
    commands = []

    CMDS = {
        'sparse': 'ip pim sparse-mode',
        'dr_prio': 'ip pim dr-priority {0}',
        'hello_interval': 'ip pim hello-interval {0}',
        'hello_auth_key': 'ip pim hello-authentication ah-md5 {0}',
        'border': 'ip pim border',
        'jp_policy_out': 'ip pim jp-policy prefix-list {0} out',
        'jp_policy_in': 'ip pim jp-policy prefix-list {0} in',
        'jp_type_in': '',
        'jp_type_out': '',
        'neighbor_policy': 'ip pim neighbor-policy prefix-list {0}',
        'neighbor_type': ''
    }

    if jp_bidir:
        if delta.get('jp_policy_in') or delta.get('jp_policy_out'):
            if existing.get('jp_type_in') == 'prefix':
                command = 'no ip pim jp-policy prefix-list {0}'.format(
                    existing.get('jp_policy_in')
                    )
            else:
                command = 'no ip pim jp-policy {0}'.format(
                    existing.get('jp_policy_in')
                    )
            if command:
                commands.append(command)

    for k, v in delta.iteritems():
        if k in ['dr_prio', 'hello_interval', 'hello_auth_key', 'border',
                 'sparse']:
            if v:
                command = CMDS.get(k).format(v)
            elif k == 'hello_auth_key':
                if isauth:
                    command = 'no ip pim hello-authentication ah-md5'
            else:
                command = 'no ' + CMDS.get(k).format(v)

            if command:
                commands.append(command)
        elif k in ['neighbor_policy', 'jp_policy_in', 'jp_policy_out',
                   'neighbor_type']:
            if k in ['neighbor_policy', 'neighbor_type']:
                temp = delta.get('neighbor_policy') or existing.get(
                    'neighbor_policy')
                if delta.get('neighbor_type') == 'prefix':
                    command = CMDS.get(k).format(temp)
                elif delta.get('neighbor_type') == 'routemap':
                    command = 'ip pim neighbor-policy {0}'.format(temp)
                elif existing.get('neighbor_type') == 'prefix':
                    command = CMDS.get(k).format(temp)
                elif existing.get('neighbor_type') == 'routemap':
                    command = 'ip pim neighbor-policy {0}'.format(temp)
            elif k in ['jp_policy_in', 'jp_type_in']:
                temp = delta.get('jp_policy_in') or existing.get(
                    'jp_policy_in')
                if delta.get('jp_type_in') == 'prefix':
                    command = CMDS.get(k).format(temp)
                elif delta.get('jp_type_in') == 'routemap':
                    command = 'ip pim jp-policy {0} in'.format(temp)
                elif existing.get('jp_type_in') == 'prefix':
                    command = CMDS.get(k).format(temp)
                elif existing.get('jp_type_in') == 'routemap':
                    command = 'ip pim jp-policy {0} in'.format(temp)
            elif k in ['jp_policy_out', 'jp_type_out']:
                temp = delta.get('jp_policy_out') or existing.get(
                    'jp_policy_out')
                if delta.get('jp_type_out') == 'prefix':
                    command = CMDS.get(k).format(temp)
                elif delta.get('jp_type_out') == 'routemap':
                    command = 'ip pim jp-policy {0} out'.format(temp)
                elif existing.get('jp_type_out') == 'prefix':
                    command = CMDS.get(k).format(temp)
                elif existing.get('jp_type_out') == 'routemap':
                    command = 'ip pim jp-policy {0} out'.format(temp)
            if command:
                commands.append(command)
        command = None

    return commands


def get_pim_interface_defaults():
    """Generates command list that will be used to default interface
       configs (not the policies) used for PIM including prioroity,
       border, hello interface, and hello auth.

    Args:
        existing (dict): key/values of the existing config
        jp_bidir (bool): flag to detrmine if join-prune policy
                         is currently configured with a single command
                         and applied in both directions

    Returns:
        List
    """
    dr_prio = '1'
    border = False
    hello_interval = '30'
    hello_auth_key = False

    args = dict(dr_prio=dr_prio, border=border,
                hello_interval=hello_interval,
                hello_auth_key=hello_auth_key)

    default = dict((param, value) for (param, value) in args.iteritems()
                   if value is not None)

    return default


def default_pim_interface_policies(existing, jp_bidir):
    """Generates command list that will be used default interface
       policies used for PIM such as neighbor and join-prune policies

    Args:
        existing (dict): key/values of the existing config
        jp_bidir (bool): flag to detrmine if join-prune policy
                         is currently configured with a single command
                         and applied in both directions

    Returns:
        List
    """
    commands = []

    if jp_bidir:
        if existing.get('jp_policy_in') or existing.get('jp_policy_out'):
                if existing.get('jp_type_in') == 'prefix':
                    command = 'no ip pim jp-policy prefix-list {0}'.format(
                        existing.get('jp_policy_in')
                        )
        if command:
            commands.append(command)

    elif not jp_bidir:
        command = None
        for k, v in existing.iteritems():
            if k == 'jp_policy_in':
                if existing.get('jp_policy_in'):
                    if existing.get('jp_type_in') == 'prefix':
                        command = 'no ip pim jp-policy prefix-list {0} in'.format(
                            existing.get('jp_policy_in')
                            )
                    else:
                        command = 'no ip pim jp-policy {0} in'.format(
                            existing.get('jp_policy_in')
                            )
            elif k == 'jp_policy_out':
                if existing.get('jp_policy_out'):
                    if existing.get('jp_type_out') == 'prefix':
                        command = 'no ip pim jp-policy prefix-list {0} out'.format(
                            existing.get('jp_policy_out')
                            )
                    else:
                        command = 'no ip pim jp-policy {0} out'.format(
                            existing.get('jp_policy_out')
                            )
            if command:
                commands.append(command)
            command = None

    if existing.get('neighbor_policy'):
        command = 'no ip pim neighbor-policy'
        commands.append(command)

    return commands


def config_pim_interface_defaults(existing, jp_bidir, isauth):
    """Generates command list to configure PIM interface settings
       to be used with Ansible modules

    Args:
        existing (dict): key/values of the existing config
        jp_bidir (bool): flag to detrmine if join-prune policy
                         is currently configured with a single command
                         and applied in both directions
        isauth (bool):   flag that states if auth is currently in place
                         for the hellos

    Returns:
        List
    """
    command = []

    # returns a dict
    defaults = get_pim_interface_defaults()
    delta = dict(set(defaults.iteritems()).difference(
                                                     existing.iteritems()))
    if delta:
        # returns a list
        command = config_pim_interface(delta, existing,
                                       jp_bidir, isauth)
    comm = default_pim_interface_policies(existing, jp_bidir)
    if comm:
        for each in comm:
            command.append(each)

    return command
