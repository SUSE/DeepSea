#!/usr/bin/python

import logging
import salt.client

__log__ = logging.getLogger(__name__)

def print_message(minion_list):
    '''
    Return a warning message about kernel-default package
    not being installed in the system
    '''
    minion_list_str = ''
    for minion in minion_list:
        minion_list_str += ' {} \n'.format(minion)

    message = '''
############################################################
ATTENTION: DeepSea detected that the following minion(s):
{}
are not running the kernel provided by kernel-default
package.
We strongly advise the user to use the kernel provided by
the kernel-default package to ensure that all Ceph services
will work correctly.

If you want DeepSea to install kernel-default package,
please rerun stage 0 as:

$ CHANGE_KERNEL=YES salt-run state.orch ceph.stage.0

Otherwise, if you want to keep the current running kernel
at your own responsability, please rerun stage 0 as:

$ KEEP_KERNEL=YES salt-run stage.orch ceph.stage.0
############################################################
    '''
    return message.format(minion_list_str)

def verify_kernel_installed(kernel_package, target_id):
    '''
    Verifies whether kernel_package is installed
    Returns True if is is installed, and False otherwise
    '''
    __log__.debug("Verifying kernel_package=%s in target_id=%s",
                  kernel_package, target_id)

    minion_list = list()
    local = salt.client.LocalClient()
    res = local.cmd(target_id, 'cmd.run',
                    ['zypper se -s kernel-* | grep "^i" | grep `uname -r | '
                     'sed "s/-default//"` | cut -d"|" -f2'], expr_form='glob')
    if len(res) == 0:
        __log__.warn('Could not verify if %s package package is installed',
                     kernel_package)
        return minion_list

    for minion in res.keys():
        output = res[minion].strip()
        __log__.debug('OUTPUT: %s', output)

        if output != kernel_package:
            minion_list.append(minion)

    return minion_list

