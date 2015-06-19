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


def get_igmp_defaults():

    flush_routes = False
    enforce_rtr_alert = False

    args = dict(flush_routes=flush_routes,
                enforce_rtr_alert=enforce_rtr_alert)

    default = dict((param, value) for (param, value) in args.iteritems() if value is not None)

    return default


def config_igmp(delta):

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
        List
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

    default = dict((param, value) for (param, value) in args.iteritems() if value is not None)

    return default


def config_igmp_snooping(delta, existing, default=False):

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

    Returns:
        Dictionary

    """
    command = 'show ip igmp interface ' + interface
    data = device.show(command)
    data_dict = xmltodict.parse(data[1])
    igmp = {}

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


def config_igmp_interface(delta):

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
        if k == 'source':
            pass
        elif k == 'prefix':
            if delta.get('source'):
                command = CMDS.get('oif_prefix_source').format(
                    delta.get('prefix'), delta.get('source'))
            else:
                command = CMDS.get('oif_prefix').format(delta.get('prefix'))
        elif v:
            command = CMDS.get(k).format(v)
        elif not v:
            command = 'no ' + CMDS.get(k).format(v)

        if command:
            commands.append(command)
        command = None

    return commands


def get_igmp_interface_defaults():

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

    default = dict((param, value) for (param, value) in args.iteritems() if value is not None)

    return default


def config_remove_oif(oif_prefix, oif_source, oif_routemap, found_both,
                      found_prefix):

    commands = []
    command = None
    if oif_routemap:
        command = 'no ip igmp static-oif route-map {0}'.format(
                                                    oif_routemap)
    if found_both:
        command = 'no ip igmp static-oif {0} source {1} '.format(
                                                    oif_prefix, oif_source)
    elif found_prefix:
        command = 'no ip igmp static-oif {0}'.format(oif_prefix)

    if command:
        commands.append(command)

    return commands

if __name__ == "__main__":

    device = Device(ip='n9396-2', username='cisco', password= '!cisco123!', protocol='http')

    interface = 'Ethernet1/33'
    existing = get_igmp_interface(device, interface)

    print json.dumps(existing, indent=4)
