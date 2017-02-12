#!/usr/bin/python

from subprocess import call, Popen, PIPE
import salt.client
import logging
import re
import os

log = logging.getLogger(__name__)

"""
Some distributions include multiple kernels and may default to a minimal
kernel in some cases.  Some Ceph services rely on  kernel modules that will
not be present in a minimal kernel.  Give the installer the best chance of
having a working cluster by replacing a minimal kernel found with a better
alternative.

For a given OS, replace the candidate kernels with the specified kernel.  For
example,

    switch kernel:
      module.run:
        - name: kernel.replace
        - kwargs:
            os:
              SUSE:
                kernel: kernel-default
                candidates:
                - kernel-default-base

"""


def replace(**kwargs):
    """
    Replace the current kernel if the kernel matches the candidates for the
    correct OS.
    """
    if __grains__['os'] in kwargs['os']:
        log.debug("os: {}".format(kwargs['os'][__grains__['os']]))
        candidates = kwargs['os'][__grains__['os']]['candidates']
        kernel = kwargs['os'][__grains__['os']]['kernel']

        package = _kernel_pkg()
        if package:
            for candidate in candidates:
                log.debug("candidate: {}".format(candidate))
                if re.match(candidate, package):
                    log.info("Installing: {}".format(kernel))
                    caller = salt.client.Caller()
                    ret = caller.cmd('pkg.install', kernel)
                    log.debug("ret: {}".format(ret))
                    return ret
        else:
            log.error("Kernel package not found")

    else:
        log.debug("No matching OS")
    return


def _kernel_pkg():
    """
    Return the package of the running kernel
    """
    kernel = open('/proc/cmdline').read()
    log.debug("/proc/cmdline: {}".format(kernel))

    boot_image = None
    try:
        boot_image = re.split(r'[= ]', kernel)[1]
        log.info("running image: {}".format(boot_image))
    except IndexError:
        log.error("BOOT_IMAGE missing")

    query = _query_command(boot_image)
    if query:
        log.debug("query: {}".format(query))
        proc = Popen(query, stdout=PIPE, stderr=PIPE)
        package = proc.stdout.read().rstrip('\n')
        log.info("package: {}".format(package))
        return package
    return

def _query_command(filename):
    """
    Determine the query command based on the package binaries.  Add others
    as needed.
    """
    if filename:
        if os.path.isfile('/bin/rpm'):
            return [ '/bin/rpm', '-qf', filename ]
        if os.path.isfile('/usr/bin/dpkg'):
            return [ '/usr/bin/dpkg', '--search', filename ]
    log.error("Neither rpm nor dpkg found")
    return

