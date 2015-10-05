import xmltodict
import os
import re
from pycsco.nxos.error import DiffError

def get_diff(device, cp_file):
    """Get a diff between running config and a proposed file.
    """
    diff_out_dict = xmltodict.parse(device.show(
        'show diff rollback-patch running-config file {0} '.format(
            cp_file), text=True)[1])
    try:
        diff_out = diff_out_dict['ins_api']['outputs']['output']['body']
    except AttributeError, KeyError:
        raise DiffError('Could not calculate diff. It\'s possible the given file doesn\'t exist.')

    return diff_out


def rollback(device, cp_file):
    """Rollback to the specified file.
    """
    rb_dict = xmltodict.parse(device.config(
        'rollback running-config file {0}'.format(
            cp_file))[1])

    rb_container = rb_dict['ins_api']['outputs']['output']

    if 'clierror' in rb_container:
        return False

    if 'body' in rb_container:
        if 'successfully' in rb_container['body']:
            return True

    return False

def save_config(device, filename):
    """Save the current running config to the given file.
    """
    device.config('copy running-config {}'.format(filename))


