try:
    import xmltodict
    from pycsco.nxos.utils import legacy
except ImportError as e:
    print '*' * 30
    print e
    print '*' * 30

__all__ = ['get_ntp_auth_cfg']

def _auth_type_to_num(auth_type):
    return '7' if auth_type == 'encrypt' else '0'


def get_ntp_auth_key(device, key_id):
    ntp_auth_cfg_response = device.show(
        'show run | inc "ntp authentication-key {0}"'.format(key_id),
         text=True)
    ntp_auth_run_cfg = xmltodict.parse(ntp_auth_cfg_response[1])\
        ['ins_api']['outputs']['output']['body']
    ntp_auth_data = legacy.get_structured_data('ntp_auth.tmpl', ntp_auth_run_cfg)
    if len(ntp_auth_data) > 0:
        return ntp_auth_data[0]

    return {}


def set_ntp_auth_key(key_id, md5string, auth_type, trusted_key, authentication):
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


def remove_ntp_auth_key(key_id, md5string, auth_type, trusted_key, authentication):
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
    if not stratrum:
        stratum = ''

    return 'ntp master {0}'.format(stratum)

def enable_ntp_logging():
    return 'ntp logging'

def enable_ntp_source(src_srcint, src_addr_int):
    return 'ntp {0} {1}'.format(
        src_srcint, src_addr_int)

def config_ntp(delta, existing):
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
            ntp_cmds.append(disable_ntp_source(existing_source_type, existing_source_addr_int))
        ntp_cmds.append(enable_ntp_source(
            source_type, source_addr_int))

    return ntp_cmds

def config_ntp_others(delta):
    auth = delta.get('auth')
    log = delta.get('log')
    master = delta.get('master')
    stratum = delta.get('stratum')
    peer = delta.get('peer')
    server = delta.get('server')
    vrf_name = delta.get('vrf_name')
    key_id = delta.get('key_id')
    prefer = delta.get('prefer')
    src = delta.get('source_addr')
    src_int = delta.get('source_int')
    trusted_key = delta.get('trusted_key')

    ntp_cmds = []

    if auth:
        ntp_cmds.append(enable_ntp_auth())
    if log:
        ntp_cmds.append(enable_ntp_logging())
    if master:
        ntp_cmds.append(enable_ntp_master(stratum))
    if peer or server:
        serv_peer = 'peer' if peer else 'server'
        ntp_cmds.append(set_ntp_server_peer(
            serv_peer, prefer, key_id, vrf_name))
    if src or src_int:
        src_srcint = 'source' if src else 'source-interface'
        src_addr_int = src if src else src_int
        ntp_cmds.append(enable_ntp_source(
            src_srcint, src_addr_int))

    return ntp_cmds

def disable_ntp_trusted_key(trusted_key):
    return 'no ntp trusted-keys {0}'.format(
        trusted_key)
    

def disable_ntp_auth():
    return 'no ntp authenticate'


def disable_ntp_server_peer(serv_peer, address):
    return 'no ntp {0} {1}'.format(
        serv_peer, address)


def disable_ntp_master(stratum):
    if not stratrum:
        stratum = ''

    return 'no ntp master {0}'.format(stratum)


def disable_ntp_logging():
    return 'no ntp logging'


def disable_ntp_source(src_srcint, src_addr_int):
    return 'no ntp {0} {1}'.format(
        src_srcint, src_addr_int)

def disable_ntp(delta):
    auth = delta.get('auth')
    log = delta.get('log')
    master = delta.get('master')
    stratum = delta.get('stratum')
    peer = delta.get('peer')
    server = delta.get('server')
    vrf_name = delta.get('vrf_name')
    key_id = delta.get('key_id')
    prefer = delta.get('prefer')
    src = delta.get('source_addr')
    src_int = delta.get('source_int')
    trusted_key = delta.get('trusted_key')

    ntp_cmds = []

    if auth:
        ntp_cmds.append(disable_ntp_auth())
    if log:
        ntp_cmds.append(disable_ntp_logging())
    if master:
        ntp_cmds.append(disable_ntp_master(stratum))
    if peer or server:
        serv_peer = 'peer' if peer else 'server'
        ntp_cmds.append(disable_ntp_server_peer(
            serv_peer, prefer, key_id, vrf_name))
    if src or src_int:
        src_srcint = 'source' if src else 'source-interface'
        src_addr_int = src if src else src_int
        ntp_cmds.append(disable_ntp_source(
            src_srcint, src_addr_int))

    return ntp_cmds


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
    ntp_log = True if 'enabled' in ntp_log_str else False
    
    return ntp_log

def get_ntp_master(device):
    response = device.show(
        'show run | inc "ntp master"', text=True)
    response_dict = xmltodict.parse(response[1])
    master_str = response_dict['ins_api']['outputs']['output']['body']
    master = True if master_str else False
    stratum = str(master_str.split()[2]) if master else None

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
    serv_peer_list = legacy.get_structured_data('ntp_server_peer.tmpl', serv_peer_str)
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


def get_ntp_existing(device, address, serv_peer):
    existing = {}

    serv_peer_list = get_ntp_serv_peer(device)
    for serv_peer_dict in serv_peer_list:
        if serv_peer_dict['address'] == address and serv_peer_dict['serv_peer'] == serv_peer:
            existing.update(serv_peer_dict)
    
    existing['serv_peer_list'] = serv_peer_list
    existing['source_type'], existing['source_addr_int'] = get_ntp_source(device)
    
    return existing

def get_ntp_auth_info(device, key_id):
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


def get_ntp_others(device):

    existing['auth'] = get_ntp_auth(device)
    existing['log'] = get_ntp_log(device)
    existing['master'], existing['stratrum'] = get_ntp_master(device)
    existing['trusted_key_list'] = get_ntp_trusted_key(device)


if __name__ == "__main__":

    device = Device(ip='n9k1', username='cisco', password='!cisco123!', protocol='http')
    ntp.get_ntp_existing(device)
# module
# test playbook
# make pretty, comment








