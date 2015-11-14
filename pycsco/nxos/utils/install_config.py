import xmltodict
from pycsco.nxos.error import DiffError


def get_diff(device, cp_file):
    """Get a diff between running config and a proposed file.
    """
    diff_out_dict = xmltodict.parse(device.show(
        'show diff rollback-patch running-config file {0} '.format(
            cp_file), text=True)[1])
    try:
        diff_out = diff_out_dict['ins_api']['outputs']['output']['body']
        diff_out = diff_out.split(
            '#Generating Rollback Patch')[1].replace(
                'Rollback Patch is Empty', '').strip()
    except (AttributeError, KeyError):
        raise DiffError(
            'Could not calculate diff. It\'s possible the given file doesn\'t exist.')

    return diff_out


def rollback(device, cp_file):
    """Rollback to the specified file.
    """
    rb_dict = xmltodict.parse(device.config(
        'rollback running-config file {0} verbose'.format(
            cp_file))[1])

    rb_container = rb_dict['ins_api']['outputs']['output']

    if 'clierror' in rb_container:
        return False

    if 'body' in rb_container:
        if 'successfully' in rb_container['body']:
            return True

    return False

def set_checkpoint(device, cp_name):
    """Set a checkpoint for current device state.
    """
    device.show('terminal dont-ask', text=True)
    device.show('checkpoint file ' + cp_name, text=True)

def save_config(device, filename):
    """Save the current running config to the given file.
    """
    device.show('checkpoint file {}'.format(filename), text=True)


def get_checkpoint(device):
    """Get a local base checkpoint file to work with.
       No file is saved on remote device.
    """
    filename = 'temp_cp_file_from_pycsco'
    set_checkpoint(device, filename)
    cp_out_dict = xmltodict.parse(device.show(
        'show file {0}'.format(
            filename), text=True)[1])

    cp_out = cp_out_dict['ins_api']['outputs']['output']['body']
    device.show('delete ' + filename, text=True)

    return cp_out
