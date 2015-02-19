Python Helper Modules for working with Cisco NX-OS Switches
=======

This is a python package that simplifies working with Cisco NX-OS switches that support NX-API.

> Note: testing thus far has been with Cisco 9396 switches running 6.1(2)I3(1) and Nexus 3064s running 6.0(2)U4(1).

# Install 

**Option 1**

```
sudo pip install pycsco
```

Using `pip` also installs a package called `xmltodict` that is used to convert xml into JSON objects.

**Option 2**

Clone this repository, modify your PYTHONPATH, and do all that fun stuff!

# INITIALIZE DEVICE

```python
>>> 
>>> import json
>>> import xmltodict
>>> 
>>> from pycsco.nxos.device import Device
>>> 
>>> switch = Device(ip='192.168.200.50',username='cisco',password='!cisco123!')
>>>
```

# EXTRACTING DATA
```python
>>> get_sh_ver = switch.show('show version') 
>>> # this returns a tuple of 2 xml objects.  the first is headers, etc. and the second is the data we want
>>>
>>> sh_ver_dict = xmltodict.parse(get_sh_ver[1]) 
>>> # converting the second element to a python dictionary
>>> 
>>> 
>>> print json.dumps(sh_ver_dict, indent=4)
{
    "ins_api": {
        "type": "cli_show", 
        "version": "1.0", 
        "sid": "eoc", 
        "outputs": {
            "output": {
                "body": {
                    "header_str": "Cisco Nexus Operating System (NX-OS) Software\nTAC support: http://www.cisco.com/tac\nCopyright (C) 2002-2014, Cisco and/or its affiliates.\nAll rights reserved.\nThe copyrights to certain works contained in this software are\nowned by other third parties and used and distributed under their own\nlicenses, such as open source.  This software is provided \"as is,\" and unless\notherwise stated, there is no warranty, express or implied, including but not\nlimited to warranties of merchantability and fitness for a particular purpose.\nCertain components of this software are licensed under\nthe GNU General Public License (GPL) version 2.0 or \nGNU General Public License (GPL) version 3.0  or the GNU\nLesser General Public License (LGPL) Version 2.1 or \nLesser General Public License (LGPL) Version 2.0. \nA copy of each such license is available at\nhttp://www.opensource.org/licenses/gpl-2.0.php and\nhttp://opensource.org/licenses/gpl-3.0.html and\nhttp://www.opensource.org/licenses/lgpl-2.1.php and\nhttp://www.gnu.org/licenses/old-licenses/library.txt.", 
                    "bios_ver_str": "07.15", 
                    "kickstart_ver_str": "6.1(2)I3(1)", 
                    "bios_cmpl_time": "06/29/2014", 
                    "kick_file_name": "bootflash:///n9000-dk9.6.1.2.I3.1.bin", 
                    "kick_cmpl_time": "9/27/2014 23:00:00", 
                    "kick_tmstmp": "09/28/2014 06:23:37", 
                    "chassis_id": "Nexus9000 C9396PX Chassis", 
                    "cpu_name": "Intel(R) Core(TM) i3-3227U C", 
                    "memory": "16402544", 
                    "mem_type": "kB", 
                    "proc_board_id": "SAL1819S6BE", 
                    "host_name": "N9K1", 
                    "bootflash_size": "21693714", 
                    "kern_uptm_days": "3", 
                    "kern_uptm_hrs": "2", 
                    "kern_uptm_mins": "8", 
                    "kern_uptm_secs": "17", 
                    "rr_reason": "Unknown", 
                    "rr_sys_ver": "6.1(2)I3(1)", 
                    "rr_service": null, 
                    "manufacturer": "Cisco Systems, Inc."
                }, 
                "input": "show version", 
                "msg": "Success", 
                "code": "200"
            }
        }
    }
}
>>> 
>>> simple = sh_ver_dict['ins_api']['outputs']['output']['body']
>>> 
>>> print simple['rr_sys_ver']
6.1(2)I3(1)
>>> 
>>> print simple['kick_file_name']
bootflash:///n9000-dk9.6.1.2.I3.1.bin

```

# PUSHING CONFIGS

```python

>>> commands = ['interface Ethernet1/1', 'no switchport', 'ip address 1.1.1.1/24', 'shutdown']
>>> 
>>> cmds_to_string = ' ; '.join(commands)  
>>> # requirement to have semi-colon between commands
>>> 
>>> print cmds_to_string
interface Ethernet1/1 ; no switchport ; ip address 1.1.1.1/24 ; shutdown
>>> 
>>> switch.config(cmds_to_string)  # can see the xml based tuple returned
(<httplib.HTTPMessage instance at 0x7ffe8b93f488>, '<?xml version="1.0"?>\n<ins_api>\n  <type>cli_conf</type>\n  <version>1.0</version>\n  <sid>eoc</sid>\n  <outputs>\n    <output>\n      <body></body>\n      <code>200</code>\n      <msg>Success</msg>\n    </output>\n    <output>\n      <body></body>\n      <code>200</code>\n      <msg>Success</msg>\n    </output>\n    <output>\n      <body></body>\n      <code>200</code>\n      <msg>Success</msg>\n    </output>\n    <output>\n      <body></body>\n      <code>200</code>\n      <msg>Success</msg>\n    </output>\n  </outputs>\n</ins_api>\n')
>>> 
>>> status = switch.config(cmds_to_string)
>>> 
>>> print json.dumps(xmltodict.parse(status[1]), indent=4)  
>>> # see return data for each command
{
    "ins_api": {
        "type": "cli_conf", 
        "version": "1.0", 
        "sid": "eoc", 
        "outputs": {
            "output": [
                {
                    "body": null, 
                    "code": "200", 
                    "msg": "Success"
                }, 
                {
                    "body": null, 
                    "code": "200", 
                    "msg": "Success"
                }, 
                {
                    "body": null, 
                    "code": "200", 
                    "msg": "Success"
                }, 
                {
                    "body": null, 
                    "code": "200", 
                    "msg": "Success"
                }
            ]
        }
    }
}
>>> 

```

# USING HELPER FUNCTIONS

```python

>>> from pycsco.nxos.utils.nxapi_lib import get_list_of_vlans
>>> 
>>> get_list_of_vlans(switch)
['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '99']
>>> 
```

```python
>>> from pycsco.nxos.utils.nxapi_lib import get_vlan
>>> 
>>> get_vlan(switch,'4')
{'vlan_state': 'active', 'admin_state': 'up', 'name': 'db', 'vlan_id': '4'}
>>> 
>>> 
```

```python

>>> from pycsco.nxos.utils.nxapi_lib import get_neighbors
>>>
>>> neigh = get_neighbors(switch,'cdp')
>>> 
>>> print json.dumps(neigh, indent=4)
[
    {
        "neighbor_interface": "FastEthernet0/22", 
        "platform": "Cisco WS-C3550-24", 
        "local_interface": "mgmt0", 
        "neighbor": "c3550"
    }, 
    {
        "neighbor_interface": "Ethernet1/2", 
        "platform": "N9K-C9396PX", 
        "local_interface": "Ethernet1/2", 
        "neighbor": "N9K2"
    }, 
    {
        "neighbor_interface": "Ethernet2/12", 
        "platform": "N9K-C9396PX", 
        "local_interface": "Ethernet2/12", 
        "neighbor": "N9K2"
    }
]
>>> 

```

## Other Functions Supported
```python

>>> from pycsco.nxos.utils.nxapi_lib import *
>>> 
>>> dir()
['__builtins__', '__doc__', '__name__', '__package__', 'cmd_list_to_string', 'create_dir', 'delete_dir', 'feature_enabled', 'get_active_vpc_peer_link', 'get_existing_portchannel_to_vpc_mappings', 'get_facts', 'get_feature_list', 'get_hsrp_group', 'get_hsrp_groups_on_interfaces', 'get_interface', 'get_interface_detail', 'get_interface_mode', 'get_interface_running_config', 'get_interface_type', 'get_interfaces_dict', 'get_ipv4_interface', 'get_list_of_vlans', 'get_min_links', 'get_mtu', 'get_neighbors', 'get_portchannel', 'get_portchannel_list', 'get_portchannel_vpc_config', 'get_switchport', 'get_system_mtu', 'get_udld_global', 'get_udld_interface', 'get_vlan', 'get_vpc', 'get_vpc_running_config', 'get_vrf', 'get_vrf_list', 'interface_is_portchannel', 'is_default', 'is_interface_copper', 'peer_link_exists', 'switch_files_list', 'vlan_range_to_list']


```

## Using Help
```python

>>> 
>>> help(get_neighbors)

Help on function get_neighbors in module pycsco.nxos.utils.nxapi_lib:

get_neighbors(device, neigh_type)
    Gets neighbors of a device
    
    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        neigh_type (str): lldp or cdp
    
    Returns:
        list: ordered list of dicts (dict per neigh)
(END)
>>>
```


