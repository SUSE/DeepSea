# -*- coding: utf-8 -*-

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

from __future__ import absolute_import
import logging
import re
import os
# pylint: disable=import-error,3rd-party-module-not-gated,redefined-builtin


log = logging.getLogger(__name__)

try:
    import salt.client
except ImportError:
    logging.error('Could not import salt.client')

try:
    from salt.exceptions import CommandExecutionError
except ImportError:
    logging.error('Could not import salt.exceptions')


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
                    caller = salt.client.Caller()
                    log.info("Removing: {}".format(candidate))
                    ret = caller.cmd('pkg.remove', candidate)
                    log.info("Installing: {}".format(kernel))
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

    query = _query_command(_boot_image(kernel))
    if query:
        log.debug("query: {}".format(query))
        _, stdout, _ = __salt__['helper.run'](query)
        package = stdout

        log.info("package: {}".format(package))
        return package
    return


def _boot_image(contents):
    """
    Return the kernel pathname parsed from the supplied string
    """
    boot_image = None
    try:
        boot_image = re.split(r'[= ]', contents)[1]
        boot_image = re.sub(r" ?\([^)]+\)", "", boot_image)
        log.info("running image: {}".format(boot_image))
    except IndexError:
        log.error("BOOT_IMAGE missing")
    return boot_image


def _query_command(filename):
    """
    Determine the query command based on the package binaries.  Add others
    as needed.
    """
    if filename:
        if os.path.isfile('/bin/rpm'):
            return ['/bin/rpm', '-qf', filename]
        if os.path.isfile('/usr/bin/dpkg'):
            return ['/usr/bin/dpkg', '--search', filename]
    log.error("Neither rpm nor dpkg found")
    return


def installed_kernel_version():
    """
    Return the installed kernel version
    """
    os_str = __grains__.get('os', '')
    if os_str == 'SUSE':
        kernel_pkgs = ['kernel-default', 'kernel-default-base']
    else:
        kernel_pkgs = ['kernel']

    for kernel_pkg in kernel_pkgs:
        try:
            pkg_info = __salt__['pkg.info_installed'](kernel_pkg)
        except CommandExecutionError:
            continue
        if pkg_info:
            pkg_info = pkg_info[kernel_pkg]
            return "{}-{}.{}".format(pkg_info['version'], pkg_info['release'], pkg_info['arch'])
    return None
