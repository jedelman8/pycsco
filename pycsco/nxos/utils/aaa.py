try:
    import xmltodict
    import re
except ImportError as e:
    print '*' * 30
    print e
    print '*' * 30

__all__ = ['get_aaa_server_info', 'config_aaa_server',
           'default_aaa_server', 'get_aaa_host_info',
           'config_aaa_host']


def _match_dict(match_list, key_map):
    no_blanks = []
    match_dict = {}

    for match_set in match_list:
        match_set = tuple(v for v in match_set if v)
        no_blanks.append(match_set)

    for info in no_blanks:
        words = info[0].strip().split()
        length = len(words)
        alt_key = key_map.get(words[0])
        first = alt_key or words[0]
        last = words[length - 1]
        match_dict[first] = last

    return match_dict


def set_aaa_server_deadtime(deadtime, server_type):
    return '{0}-server deadtime {1}'.format(server_type, deadtime)


def remove_aaa_server_deadtime(server_type):
    return 'no {0}-server deadtime 1'.format(server_type)


def set_aaa_server_timeout(timeout, server_type):
    return '{0}-server timeout {1}'.format(server_type, timeout)


def remove_aaa_server_timeout(server_type):
    return 'no {0}-server timeout 1'.format(server_type)


def enable_aaa_server_dir_req(server_type):
    return '{0}-server directed-request'.format(server_type)


def disable_aaa_server_dir_req(server_type):
    return 'no {0}-server directed-request'.format(server_type)


def set_aaa_server_global_key(encrypt_type, key, server_type):
    if not encrypt_type:
        encrypt_type = ''
    return '{0}-server key {1} {2}'.format(
        server_type, encrypt_type, key)


def remove_aaa_server_global_key(server_type):
    return 'no {0}-server key'.format(server_type)


def get_aaa_server_info(device, server_type):
    aaa_server_info = {}

    response = device.show(
        'show {0}-server'.format(server_type), text=True)
    response_dict = xmltodict.parse(response[1])
    response_text = response_dict['ins_api']['outputs']['output']['body']
    response_lines = response_text.split('\n')

    for line in response_lines:
        if line.startswith('timeout'):
            aaa_server_info['timeout'] = line.split(':')[1]
        elif line.startswith('deadtime'):
            aaa_server_info['deadtime'] = line.split(':')[1]

    response = device.show(
        'show {0}-server directed-request'.format(server_type), text=True)
    response_dict = xmltodict.parse(response[1])
    response_text = response_dict['ins_api']['outputs']['output']['body']
    aaa_server_info['directed_request'] = response_text

    return aaa_server_info


def config_aaa_server(params, server_type):
    '''Returns a list of commands for global AAA settings.

    Args:
        params (dictionary): A dictionary of parameters
        server_type (string): "radius" or "tacacs"

    Returns:
        A list of commands (strings) for configuring the global AAA settings.
    '''
    cmds = []

    deadtime = params.get('deadtime')
    timeout = params.get('timeout')
    directed_request = params.get('directed_request')
    encrypt_type = params.get('encrypt_type')
    global_key = params.get('global_key')

    if deadtime:
        cmds.append(set_aaa_server_deadtime(deadtime, server_type))
    if timeout:
        cmds.append(set_aaa_server_timeout(timeout, server_type))
    if directed_request:
        if directed_request == 'enabled':
            cmds.append(enable_aaa_server_dir_req(server_type))
        elif directed_request == 'disabled':
            cmds.append(disable_aaa_server_dir_req(server_type))
    if global_key:
        cmds.append(set_aaa_server_global_key(
            encrypt_type, global_key, server_type))

    return cmds


def default_aaa_server(params, server_type):
    '''Returns a list of commands to default global AAA settings.

    Args:
        params (dictionary): A dictionary of parameters to be defaulted
        server_type (bool): "radius" or "tacacs"

    Returns:
        A list of commands (strings) for defaulting the global AAA settings.
    '''
    cmds = []

    deadtime = params.get('deadtime')
    timeout = params.get('timeout')
    directed_request = params.get('directed_request')
    global_key = params.get('global_key')

    if deadtime:
        cmds.append(remove_aaa_server_deadtime(server_type))
    if timeout:
        cmds.append(remove_aaa_server_timeout(server_type))
    if directed_request:
        cmds.append(disable_aaa_server_dir_req(server_type))
    if global_key:
        cmds.append(remove_aaa_server_global_key(server_type))

    return cmds


def get_aaa_host_info(device, server_type, address):
    '''Returns a dictionary of configured parameters for a given AAA host.

    Args:
        device (Device): NX-API enabled device from which to retrieve configration
        server_type (bool): "radius" or "tacacs"
        address (string): IP address or network name that identifies the AAA host

    Returns:
        A dictionary of configured parameters for the given AAA host.
    '''
    aaa_host_info = {}

    response = device.show(
        'sh run | inc "{0}-server host {1}"'.format(
            server_type, address), text=True)
    response_dict = xmltodict.parse(response[1])
    response_text = response_dict['ins_api']['outputs']['output']['body']

    if not response_text:
        return {}

    pattern =\
        '(acct-port \d+)|(timeout \d+)|(auth-port \d+)|(key 7 "\w+")|( port \d+)'
    raw_match = re.findall(pattern, response_text)
    aaa_host_info =\
        _match_dict(
            raw_match, {'acct-port': 'acct_port',
                        'auth-port': 'auth_port',
                        'port': 'tacacs_port'})

    return aaa_host_info


def config_aaa_host(server_type, address, params, clear=False):
    '''Returns a list of commands for host-specific AAA settings.

    Args:
        server_type (string): "radius" or "tacacs"
        address (string): IP address or network name that identifies the AAA host
        params (dictionary): A dictionary of parameters
        clear (bool): Whether the configuration should be cleared first

    Returns:
        A list of commands (strings) for configuring the host-specific AAA settings.
    '''
    cmds = []

    if clear:
        cmds.append('no {0}-server host {1}'.format(server_type, address))

    cmd_str = '{0}-server host {1}'.format(server_type, address)

    key = params.get('key')
    enc_type = params.get('encrypt_type', '')
    timeout = params.get('timeout')
    auth_port = params.get('auth_port')
    acct_port = params.get('acct_port')
    port = params.get('tacacs_port')

    if auth_port:
        cmd_str += ' auth-port {0}'.format(auth_port)
    if acct_port:
        cmd_str += ' acct-port {0}'.format(acct_port)
    if port:
        cmd_str += ' port {0}'.format(port)
    if timeout:
        cmd_str += ' timeout {0}'.format(timeout)
    if key:
        cmds.append('{0}-server host {1} key {2} {3}'.format(server_type, address, enc_type, key))

    cmds.append(cmd_str)

    return cmds
