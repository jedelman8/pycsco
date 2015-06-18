from pycsco.nxos.device import Device
from pycsco.nxos.utils import nxapi_lib

try:
	import xmltodict
except ImportError as e:
    print '*' * 30
    print e
    print '*' * 30


def get_vtp_current_cfg(device):
	'''Gets the current vtp configuration on a given device

	Args:
		device (Device): NX-API enabled device from which to retrieve configration

	Returns:
		dictionary of VTP configuration parameters
	'''	
	status_dict = xmltodict.parse(device.show('show vtp status')[1])
	current_from_device = status_dict['ins_api']['outputs']['output']['body']

	current = {}
	current['version'] = str(current_from_device['running-version'])
	if current_from_device['domain_name']:
		current['domain'] = str(current_from_device['domain_name'])
	else:
		current['domain'] = None
	current['vtp_password'] = get_vtp_password(device)	

	return current

def get_vtp_password(device):
	'''Gets the current vtp password on a given device

	Args:
		device (Device): NX-API enabled device from which to retrieve password

	Returns:
		dictionary of VTP configuration parameters
	'''	
	pass_dict = xmltodict.parse(device.show('show vtp password')[1])
	password = pass_dict['ins_api']['outputs']['output']['body']['passwd']
	if password:
		return str(password)

