try:
    import xmltodict
    from pycsco.nxos.utils import legacy
except ImportError as e:
    print '*' * 30
    print e
    print '*' * 30

__all__ = []

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

def config_aaa_server(params, server_type):
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
