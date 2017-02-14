#!/usr/bin/python

import logging
import re
from subprocess import Popen, PIPE

__log__ = logging.getLogger(__name__)

def verify_kernel_installed(kernel_package):
    '''
    Verifies whether kernel_package is installed
    Returns True if is is installed, and False otherwise
    '''

    __log__.debug("Verifying kernel_package %s", kernel_package)

    # zypper se -s kernel-* | grep "^i" | grep `uname -r | \
    #                         sed "s/-default//"` | cut -d"|" -f2

    proc = Popen(['uname', '-r'], stdout=PIPE)
    uname_out = proc.stdout.read().strip()
    match = re.search(r'(.+)-default', uname_out)
    if match is None:
        __log__.warn('Could not verify if %s package package is installed',
                     kernel_package)
        return True

    kernel_ver = match.group(1).strip()

    proc_zyp = Popen(['zypper', 'se', '-s', 'kernel-*'], stdout=PIPE)
    proc_grep1 = Popen(['grep', '^i'], stdin=PIPE, stdout=PIPE)
    proc_grep2 = Popen(['grep', kernel_ver], stdin=PIPE, stdout=PIPE)
    proc_cut = Popen(['cut', '-d|', '-f2'], stdin=PIPE, stdout=PIPE)

    grep1_out = proc_grep1.communicate(input=proc_zyp.communicate()[0])
    grep2_out = proc_grep2.communicate(input=grep1_out[0])
    output = proc_cut.communicate(input=grep2_out[0])[0].strip()

    __log__.debug('OUTPUT: %s', output)

    if output is None:
        __log__.warn('Could not verify if %s package package is installed',
                     kernel_package)

    if output != kernel_package:
        return False

    return True

