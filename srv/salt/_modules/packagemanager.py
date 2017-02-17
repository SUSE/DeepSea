from subprocess import Popen, PIPE
import platform
import logging
import os

log = logging.getLogger(__name__)


class PackageManager(object):

    """
    That is not the nativ salt module and is not ment to
    replace it.
    This module was created to react on packagemanagers
    reboot advice.
    """

    def __init__(self, **kwargs):
        self.debug = kwargs.get('debug', False)
        self.kernel = kwargs.get('kernel', False)

        self.platform = platform.linux_distribution()[0].lower()
        if "suse" in self.platform or "opensuse" in self.platform:
            log.info("Found {}. Using {}".format(self.platform, Zypper.__name__))
            # Ceck if PM is installed?
            self.pm = Zypper(**kwargs)
        elif "fedora" in self.platform or "centos" in self.platform:
            log.info("Found {}. Using {}".format(self.platform, Apt.__name__))
            # Ceck if PM is installed?
            self.pm = Apt(**kwargs)
        else:
            raise ValueError("Failed to detect PackageManager for OS."
                             "Open an issue on github.com/SUSE/DeepSea")

    def reboot(self):
        """
        Assuming `shutdown -r` works on all platforms
        """
        log.info("The PackageManager asked for a systemreboot. Rebooting")
        if self.debug:
            log.debug("INITIALIZING REBOOT")
            return None
        cmd = "shutdown -r"
        Popen(cmd, stdout=PIPE)


class Apt(PackageManager):

    VERSION = 0.1

    def __init__(self, **kwargs):
        pass

    def _updates_needed(self):
        cmd = 'apt-get -u upgrade'
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        proc.wait()
        # UNTESTED
        if proc.returncode != 0:
            log.info('Update Needed')
            return True
        else:
            log.info('No Update Needed')
            return False

    def refresh(self):
        cmd = 'apt-get -y update'
        Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)

    def _handle(self, strat='up'):
        if strat == 'up':
            strat = 'upgrade'
        if self._updates_needed():
            base_flags = ['--yes']
            strategy_flags = ["-o Dpkg::Options::=", "--force-confnew",
                              "--force-yes", "-fuy"]
            cmd = "apt-get {base_flags} {strategy} {strategy_flags}".\
                   format(base_flags=base_flags,
                          strategy=strat, 
                          strategy_flags=strategy_flags)
            proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
            proc.wait()
            for line in proc.stdout:
                log.info(line)
            for line in proc.stderr:
                log.info(line)
            log.info("returncode: {}".format(proc.returncode))
            if os.path.isfile('/var/run/reboot-required'):
                self.reboot()
        else:
            log.info('System up to date')


class Zypper(PackageManager):

    """
    Although salt already has a zypper module
    the upgrading workflow is much cleaner if
    deepsea handles reboots based on the returncode
    from zypper. In order to react on those
    Zypper has to be invoked in a separate module.

    notes on :kernel:
    if you pass the --non-interactive flag
    zypper won't pull in kernel updates.
    To also upgrade the kernel I created this
    flag.
    """

    RETCODES = {102: 'ZYPPER_EXIT_INF_REBOOT_NEEDED',
                100: 'ZYPPER_EXIT_INF_UPDATE_NEEDED'}

    VERSION = 0.1

    def __init__(self, **kwargs):
        pass

    def _refresh(self):
        log.info("Refreshing Repositories..")
        cmd = "zypper --non-interactive refresh"
        Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)

    def _updates_needed(self):
        """
        Updates that are sourced from all Repos
        """
        self._refresh()
        cmd = "zypper lu | grep -sq 'No updates found'"
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        proc.wait()
        if proc.returncode != 0:
            log.info('Update Needed')
            return True
        else:
            log.info('No Update Needed')
            return False

    def _patches_needed(self):
        """
        Updates that are sourced from an official Update
        Repository
        """
        cmd = "zypper --non-interactive patch-check"
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        proc.wait()
        if proc.returncode == 100:
            log.info(self.RETCODES[proc.returncode])
            log.info('Patches Needed')
            return True
        else:
            log.info('No Patches Needed')
            return False

    def _handle(self, strat='up'):
        """
        Conbines up and dup and executes the constructed zypper command.
        """
        if self._updates_needed():
            zypper_flags = ['--non-interactive']
            strategy_flags = ['--replacefiles', '--auto-agree-with-licenses']
            cmd = "zypper {zypper_flags} {strategy} {strategy_flags}".\
                   format(zypper_flags=zypper_flags,
                          strategy=strat, 
                          strategy_flags=strategy_flags)
            proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
            proc.wait()
            for line in proc.stdout:
                log.info(line)
            for line in proc.stderr:
                log.info(line)
            log.info("returncode: {}".format(proc.returncode))

            if proc.returncode == 102:
                log.info(self.RETCODES[proc.returncode])
                log.info('Reboot required')
                self.reboot()
            if proc.returncode <= 100:
                log.info('Zyppers returncode < 100 indicates a failure')
                raise StandardError('Zypper failed. Look at the logs')
        else:
            log.info('System up to date')


def up(**kwargs):
    strat = up.__name__
    obj = PackageManager(**kwargs)
    obj.pm._handle(strat=strat)


def dup(**kwargs):
    strat = dup.__name__
    obj = PackageManager(**kwargs)
    obj.pm._handle(strat=strat)
