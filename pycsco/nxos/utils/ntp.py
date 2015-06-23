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


def set_ntp_auth_key(key_id, md5string, auth_type):
    ntp_auth_cmds = []
    auth_type_num = _auth_type_to_num(auth_type)
    ntp_auth_cmds.append(
        'ntp authentication-key {0} md5 {1} {2}'.format(
        key_id, md5string, auth_type_num))

    return ntp_auth_cmds


def remove_ntp_auth_key(key_id, md5string, auth_type):
    auth_remove_cmds = []
    auth_type_num = _auth_type_to_num(auth_type)
    auth_remove_cmds.append(
        'no ntp authentication-key {0} md5 {1} {2}'.format(
            key_id, md5string, auth_type_num))
    
    return auth_remove_cmds


def set_ntp_trusted_key(trusted_key):
    enable_tk_cmds = []
    enable_tk_cmds.append('ntp trusted-keys {0}'.format(
        trusted_key))
    
    return enable_tk_cmds


def enable_ntp_auth():
    return ['ntp authenticate']


def set_ntp_peer_server(peer_serv, prefer, key_id, vrf_name):
    prefer_str = 'prefer' if prefer else ''
    if not key_id:
        key_id = ''
    if not vrf_name:
        vrf_name = ''
    
    return ['ntp {0} {1} {2} {3}'.format(
        peer_serv, prefer_str, key_id, vrf_name)]

def enable_ntp_master(stratum):
    if not stratrum:
        stratum = ''

    return ['ntp master {0}'.format(stratum)]

def enable_ntp_logging():
    return ['ntp logging']

def enable_source(src_srcint, src_addr_int):
    return ['ntp {0} {1}'.format(
        src_srcint, src_addr_int)]


# single function for configuration
# disable counterparts
# single function for disabilization
# get_current for each
# single function for current state
# module
# test playbook
# make pretty, comment








