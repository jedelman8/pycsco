try:
    import xmltodict
    from pycsco.nxos.utils import legacy
except ImportError as e:
    print '*' * 30
    print e
    print '*' * 30

__all__ = ['get_ntp_existing', 'config_ntp', 'disable_ntp_server_peer',
           'get_ntp_auth_info', 'set_ntp_auth_key', 'remove_ntp_auth_key',
           'config_ntp_options', 'get_ntp_options']


def _auth_type_to_num(auth_type):
    return '7' if auth_type == 'encrypt' else '0'


def set_ntp_trusted_key(trusted_key):
    return 'ntp trusted-keys {0}'.format(
        trusted_key)


def enable_ntp_auth():
    return 'ntp authenticate'


def set_ntp_server_peer(serv_peer, address, prefer, key_id, vrf_name):
    prefer_str = 'prefer' if prefer else ''
    key_str = 'key {0}'.format(key_id) if key_id else ''
    vrf_str = 'use-vrf {0}'.format(vrf_name) if vrf_name else ''

    return 'ntp {0} {1} {2} {3} {4}'.format(
        serv_peer, address, prefer_str, key_str, vrf_str)


def enable_ntp_master(stratum):
    if not stratum:
        stratum = ''

    return 'ntp master {0}'.format(stratum)


def enable_ntp_logging():
    return 'ntp logging'


def enable_ntp_source(src_srcint, src_addr_int):
    return 'ntp {0} {1}'.format(
        src_srcint, src_addr_int)


def disable_ntp_trusted_key(trusted_key):
    return 'no ntp trusted-keys {0}'.format(
        trusted_key)


def disable_ntp_auth():
    return 'no ntp authenticate'


def disable_ntp_master():
    return 'no ntp master'


def disable_ntp_logging():
    return 'no ntp logging'


def get_ntp_auth_key(device, key_id):
    ntp_auth_cfg_response = device.show(
        'show run | inc "ntp authentication-key {0}"'.format(key_id),
        text=True)
    ntp_auth_run_cfg = xmltodict.parse(
        ntp_auth_cfg_response[1])['ins_api']['outputs']['output']['body']
    ntp_auth_data = legacy.get_structured_data(
        'ntp_auth.tmpl', ntp_auth_run_cfg)
    if len(ntp_auth_data) > 0:
        return ntp_auth_data[0]

    return {}


def get_ntp_auth(device):
    response = device.show(
        'show ntp authentication-status')
    response_dict = xmltodict.parse(response[1])
    ntp_auth_str = response_dict['ins_api']['outputs']['output']['body']['authentication']
    ntp_auth = True if 'enabled' in ntp_auth_str else False

    return ntp_auth


def get_ntp_log(device):
    response = device.show(
        'show ntp logging')
    response_dict = xmltodict.parse(response[1])
    ntp_log_str = response_dict['ins_api']['outputs']['output']['body']['loggingstatus']
    ntp_log = 'true' if 'enabled' in ntp_log_str else 'false'

    return ntp_log


def get_ntp_master(device):
    response = device.show(
        'show run | inc "ntp master"', text=True)
    response_dict = xmltodict.parse(response[1])
    master_str = response_dict['ins_api']['outputs']['output']['body']
    master = 'true' if master_str else 'false'
    stratum = str(master_str.split()[2]) if master == 'true' else None

    return master, stratum


def get_ntp_trusted_key(device):
    trusted_key_list = []

    response = device.show(
        'show run | inc "ntp trusted-key"', text=True)
    response_dict = xmltodict.parse(response[1])
    trusted_key_str = response_dict['ins_api']['outputs']['output']['body']
    trusted_keys = trusted_key_str.split('\n') if trusted_key_str else []
    for line in trusted_keys:
        trusted_key_list.append(str(line.split()[2]))

    return trusted_key_list


def get_ntp_serv_peer(device):
    response = device.show(
        'show run | inc "ntp (server|peer)"', text=True)
    response_dict = xmltodict.parse(response[1])
    serv_peer_str = response_dict['ins_api']['outputs']['output']['body']
    serv_peer_list = legacy.get_structured_data(
        'ntp_server_peer.tmpl', serv_peer_str)
    for serv_peer in serv_peer_list:
        if serv_peer['prefer']:
            serv_peer['prefer'] = 'enabled'
        else:
            serv_peer['prefer'] = 'disabled'

    return serv_peer_list


def get_ntp_source(device):
    source_type = None
    source_addr_int = None

    response = device.show(
        'show run | inc "ntp source"', text=True)
    response_dict = xmltodict.parse(response[1])
    source_text = response_dict['ins_api']['outputs']['output']['body']
    if source_text:
        if 'interface' in source_text:
            source_type = 'source-interface'
        else:
            source_type = 'source'

        source_addr_int = source_text.split()[2].lower()

    return source_type, source_addr_int


def set_ntp_auth_key(key_id, md5string, auth_type, trusted_key, authentication):
    '''Returns a list of commands to set an NTP authentication key

    Args:
        key_id (string): key identifier (numeric)
        md5string (string): md5string to be used with the key
        auth_type (string): "encrypt" or "text", representing the state of the md5string
        trusted_key (string): "true" or "false", representing whether the key is trusted
        authentication (string): "on" or "off", representing the state of the authentication process

    Returns:
        A list of commands (strings) for configuring the NTP authentication key.
    '''
    ntp_auth_cmds = []
    auth_type_num = _auth_type_to_num(auth_type)
    ntp_auth_cmds.append(
        'ntp authentication-key {0} md5 {1} {2}'.format(
            key_id, md5string, auth_type_num))

    if trusted_key == 'true':
        ntp_auth_cmds.append(
            'ntp trusted-key {0}'.format(key_id))
    elif trusted_key == 'false':
        ntp_auth_cmds.append(
            'no ntp trusted-key {0}'.format(key_id))

    if authentication == 'on':
        ntp_auth_cmds.append(
            'ntp authenticate')
    elif authentication == 'off':
        ntp_auth_cmds.append(
            'no ntp authenticate')

    return ntp_auth_cmds


def config_ntp_options(delta, flip=False):
    '''Returns a list of commands to set NTP optional parameters.
       Options include:
        - toggling the device as an authoritative NTP server
        - toggling the device for NTP logging

    Args:
        delta (dictionary): A dictionary of parameters
        flip (bool): Whether to reverse the parameters, defaults to False.

    Returns:
        A list of commands (strings) for configuring the NTP optional parameters.
    '''
    master = delta.get('master')
    stratum = delta.get('stratum')
    log = delta.get('logging')

    if flip:
        if log == 'true':
            log = 'false'
        elif log == 'false':
            log = 'true'
        if master == 'true':
            master = 'false'
        elif master == 'false':
            master = 'true'

    ntp_cmds = []

    if log:
        if log == 'true':
            ntp_cmds.append(enable_ntp_logging())
        elif log == 'false':
            ntp_cmds.append(disable_ntp_logging())
    if master:
        if master == 'true':
            ntp_cmds.append(enable_ntp_master(stratum))
        elif master == 'false':
            ntp_cmds.append(disable_ntp_master())

    return ntp_cmds


def config_ntp(delta, existing):
    '''Returns the configuration commands for configuring an NTP peer or server
       using the given parameters.

    Args:
        delta (dictionary): The primary dictionary of parameters
        existing (dictionary): The secondary dictionary of parameters

    Returns:
        A list of configuration command(s) for configuring NTP with the given parameters
    '''
    address = delta.get('address')
    serv_peer = delta.get('serv_peer')
    vrf_name = delta.get('vrf_name')
    key_id = delta.get('key_id')
    prefer = delta.get('prefer')

    if address or serv_peer or vrf_name or key_id or prefer:
        address = delta.get('address', existing.get('address'))
        serv_peer = delta.get('serv_peer', existing.get('serv_peer'))
        vrf_name = delta.get('vrf_name', existing.get('vrf_name'))
        key_id = delta.get('key_id', existing.get('key_id'))
        prefer = delta.get('prefer', existing.get('prefer'))

    if prefer:
        if prefer == 'enabled':
            prefer = True
        elif prefer == 'disabled':
            prefer = False

    source_type = delta.get('source_type')
    source_addr_int = delta.get('source_addr_int')
    if source_addr_int:
        source_type = delta.get('source_type', existing.get('source_type'))

    ntp_cmds = []

    if serv_peer:
        ntp_cmds.append(set_ntp_server_peer(
            serv_peer, address, prefer, key_id, vrf_name))
    if source_addr_int:
        existing_source_type = existing.get('source_type')
        existing_source_addr_int = existing.get('source_addr_int')
        if existing_source_type and source_type != existing_source_type:
            ntp_cmds.append(disable_ntp_source(
                existing_source_type, existing_source_addr_int))
        ntp_cmds.append(enable_ntp_source(
            source_type, source_addr_int))

    return ntp_cmds


def remove_ntp_auth_key(key_id, md5string, auth_type, trusted_key, authentication):
    '''Returns a list of commands to remove an NTP authentication key

    Args:
        key_id (string): key identifier (numeric)
        md5string (string): md5string to be used with the key
        auth_type (string): "encrypt" or "text", representing the state of the md5string
        trusted_key (string): "true" or "false", representing whether the key is trusted
        authentication (string): "on" or "off", representing the state of the authentication process

    Returns:
        A list of commands (strings) for removing the NTP authentication key.
    '''
    auth_remove_cmds = []
    auth_type_num = _auth_type_to_num(auth_type)
    auth_remove_cmds.append(
        'no ntp authentication-key {0} md5 {1} {2}'.format(
            key_id, md5string, auth_type_num))

    if authentication == 'on':
        auth_remove_cmds.append(
            'no ntp authenticate')
    elif authentication == 'off':
        auth_remove_cmds.append(
            'ntp authenticate')

    return auth_remove_cmds


def disable_ntp_server_peer(serv_peer, address):
    '''Returns the command to disable a given NTP server or peer

    Args:
        serv_peer (string): "server" or "peer"
        address (string): Address of server or peer

    Returns:
        A string for disabling the given NTP server or peer
    '''
    return 'no ntp {0} {1}'.format(
        serv_peer, address)


def disable_ntp_source(src_srcint, src_addr_int):
    '''Returns the command to disable a given NTP source address or interface

    Args:
        src_srcint (string): "source" for source address, "source-interface" for source interface
        src_addr_int (string): The name of the address or interface

    Returns:
        A string for disabling the given NTP source address or interface
    '''
    return 'no ntp {0} {1}'.format(
        src_srcint, src_addr_int)


def get_ntp_existing(device, address, serv_peer):
    '''Returns the NTP configuration on a given device for a specified server or peer.

    Args:
        device (Device): NX-API enabled device from which to retrieve configration
        address (string): Address of server or peer
        serv_peer (string): "server" or "peer"

    Returns:
        A dictionary of NTP configuration parameters for the server or peer
    '''
    existing = {}

    serv_peer_list = get_ntp_serv_peer(device)
    for serv_peer_dict in serv_peer_list:
        if serv_peer_dict['address'] == address:
            if serv_peer_dict['serv_peer'] == serv_peer:
                existing.update(serv_peer_dict)

    existing['serv_peer_list'] = serv_peer_list
    existing['source_type'], existing['source_addr_int'] = get_ntp_source(device)

    return existing


def get_ntp_auth_info(device, key_id):
    '''Returns the NTP authentication configuration on a given device.

    Args:
        device (Device): NX-API enabled device from which to retrieve configration
        key_id (string): authentication key identifier (numeric)

    Returns:
        A dictionary of NTP authentication configuration parameters
    '''
    auth_info = get_ntp_auth_key(device, key_id)
    trusted_key_list = get_ntp_trusted_key(device)
    auth_power = get_ntp_auth(device)

    if key_id in trusted_key_list:
        auth_info['trusted_key'] = 'true'
    else:
        auth_info['trusted_key'] = 'false'

    if auth_power:
        auth_info['authentication'] = 'on'
    else:
        auth_info['authentication'] = 'off'

    return auth_info


def get_ntp_options(device):
    '''Returns the NTP optional parameters on a given device.

    Args:
        device (Device): NX-API enabled device from which to retrieve configration

    Returns:
        A dictionary of NTP optional parameters
    '''
    existing = {}
    existing['logging'] = get_ntp_log(device)
    existing['master'], existing['stratum'] = get_ntp_master(device)

    return existing
