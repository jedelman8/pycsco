from pycsco.nxos.error import InputError
from pycsco.lib import ipaddr

try:
    import xmltodict
except ImportError as e:
    print '*' * 30
    print e
    print '*' * 30


__all__ = ['normalize_prefix', 'get_static_routes']


def _route_id_tag(prefix, next_hop):
    return str(prefix) + ',' + str(next_hop)


def _pop_route_dict(fields):
    route_dict = {}
    arg_name = ''
    arg_flag = False
    for j in range(4, len(fields)):
        if arg_flag:
            arg_flag = False
        else:
            arg_flag = True

        if arg_name:
            route_dict[arg_name] = str(fields[j])
            arg_name = ''
        elif fields[j] == 'tag':
            arg_name = 'tag'
        elif fields[j] == 'name':
            arg_name = 'route_name'
        else:
            if arg_flag and j == len(fields) - 1:
                route_dict['pref'] = str(fields[j])

    return route_dict


def _parse_vrf_static_routes(run_config):
    vrf_route_dict = {}
    lines = run_config.split('\n')

    for i in range(1, len(lines)):
        line = lines[i].strip()
        if line.startswith('ip route'):
            fields = line.split()
            prefix = fields[2]
            next_hop = fields[3]
            vrf_route_dict[_route_id_tag(prefix, next_hop)] = \
                _pop_route_dict(fields)

    return vrf_route_dict


def _parse_default_static_routes(run_config):
    default_dict = {}
    lines = run_config.split('\n')

    for i in range(len(lines)):
        line = lines[i].strip()
        fields = line.split()
        prefix = fields[2]
        next_hop = fields[3]
        default_dict[_route_id_tag(prefix, next_hop)] = _pop_route_dict(fields)

    return default_dict


def _get_vrf_static_routes(device, vrf_name, prefix, next_hop):
    vrf_context_output = device.show(
        'show run | sec "vrf context {0}"'.format(vrf_name), text=True)
    vrf_context_dict = xmltodict.parse(vrf_context_output[1])
    vrf_run_config = vrf_context_dict['ins_api']['outputs']['output']['body']

    if vrf_run_config:
        vrf_static_routes = _parse_vrf_static_routes(vrf_run_config)
        normalized_prefix = normalize_prefix(prefix)
        id_tag = _route_id_tag(normalized_prefix, next_hop)
        return vrf_static_routes.get(id_tag)


def _get_default_vrf_static_routes(device, prefix, next_hop):
    default_static_output = \
        device.show('show run | inc "^ip route"', text=True)
    default_static_dict = xmltodict.parse(default_static_output[1])
    default_static_run_config = \
        default_static_dict['ins_api']['outputs']['output']['body']

    if default_static_run_config:
        default_static_routes = \
            _parse_default_static_routes(default_static_run_config)
        normalized_prefix = normalize_prefix(prefix)
        id_tag = _route_id_tag(normalized_prefix, next_hop)
        return default_static_routes.get(id_tag)


def normalize_prefix(prefix):
    '''Returns the network IP address of a given IP address and mask

    Args:
        prefix (string): IP address and mask concatenated by '/', e.g. '192.168.1.3/24'

    Returns:
        A string representing the network IP address and mask
    '''
    if '/' not in prefix:
        raise InputError('Prefix must use / notation.')

    mask = prefix.split('/')[1]
    try:
        network = ipaddr.IPv4Network(prefix).network.exploded
    except:
        raise InputError('Invalid address')

    return network + '/' + mask


def get_static_routes(device, vrf, prefix, next_hop):
    '''Returns the static route for a given device, vrf, prefix and next hop

    Args:
        device (Device): NX-API enabled device from which to retrieve configration
        vrf (string): The VRF of the given static route
        prefix (string): The prefix of the given static route
        next_hop (string): The next hop of the given static route

    Returns:
        A dictionary representing the attributes of the static route if there is one.
        Returns an empty dictionary otherwise.
    '''
    if vrf == 'default':
        static_routes = _get_default_vrf_static_routes(device, prefix, next_hop)
    else:
        static_routes = _get_vrf_static_routes(device, vrf, prefix, next_hop)

    if static_routes is not None:
        static_routes['prefix'] = normalize_prefix(prefix)
        static_routes['next_hop'] = next_hop
        static_routes['vrf'] = vrf
        return static_routes

    return {}


def config_static_route(vrf, prefix, next_hop, delta, existing):
    '''Returns the configuration string(s) for configuring the static route

    Args:
        vrf (string): The VRF of the given static route
        prefix (string): The prefix of the given static route
        next_hop (string): The next hop of the given static route
        delta (dictionary): Primary dictionary of static route configuration parameters
        existing (dictionary): Secondary dictionary of static route configuration parameters

    Returns:
        A list of configuration string(s) that configures the static route
    '''
    static_route_cmds = []
    if vrf != 'default':
        static_route_cmds.append('vrf context {0}'.format(vrf))

    route_cmd = 'ip route {0} {1}'.format(prefix, next_hop)
    route_name = delta.get('route_name', existing.get('route_name'))
    tag = delta.get('tag', existing.get('tag'))
    pref = delta.get('pref', existing.get('pref'))

    if route_name:
        route_cmd += ' name {0}'.format(route_name)
    if tag:
        route_cmd += ' tag {0}'.format(tag)
    if pref:
        route_cmd += ' {0}'.format(pref)

    static_route_cmds.append(route_cmd)
    return static_route_cmds


def remove_static_route(vrf, prefix, next_hop):
    '''Returns the configuration string(s) for removing the given static route

    Args:
        vrf (string): The VRF of the given static route
        prefix (string): The prefix of the given static route
        next_hop (string): The next hop of the given static route

    Returns:
        A list of configuration string(s) that removes the given static route
    '''
    static_route_cmds = []
    if vrf != 'default':
        static_route_cmds.append('vrf context {0}'.format(vrf))

    route_cmd = 'no ip route {0} {1}'.format(prefix, next_hop)
    static_route_cmds.append(route_cmd)
    return static_route_cmds
