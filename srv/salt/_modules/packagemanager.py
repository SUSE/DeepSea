from subprocess import Popen, PIPE
from platform import linux_distribution
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
        self.reboot = kwargs.get('reboot', True)

        self.platform = linux_distribution()[0].lower()
        if "suse" in self.platform or "opensuse" in self.platform:
            log.info("Found {}. Using {}".format(self.platform, Zypper.__name__))
            self.pm = Zypper(**kwargs)
        elif "fedora" in self.platform or "centos" in self.platform:
            log.info("Found {}. Using {}".format(self.platform, Apt.__name__))
            self.pm = Apt(**kwargs)
        else:
            raise ValueError("Failed to detect PackageManager for OS."
                             "Open an issue on github.com/SUSE/DeepSea")

    def reboot_in(self):
        """
        Assuming `shutdown -r` works on all platforms
        """
        log.info("The PackageManager asked for a systemreboot. Rebooting in 1 Minute")
        if self.debug or not self.reboot:
            log.debug("Faking Reboot")
            return None
        log.debug("Initializing Reboot.")
        cmd = "shutdown -r"
        Popen(cmd, stdout=PIPE, shell=True)


class Apt(PackageManager):

    VERSION = 0.1

    def __init__(self, **kwargs):
        """
        Instead of reinitializing __init__ from super,
        the child get kwargs passed as arguments to
        have the possibility to handle those differently.
        """
        self.kernel = kwargs.get('kernel', False)
        self.debug = kwargs.get('debug', False)
        self.reboot = kwargs.get('reboot', True)
        self.base_flags = ['--yes']

    def _updates_needed(self):
        """
        Checking the output of apt-check for
        (1) Regular updates
        (2) Security updates
        Content is written to stderr
        """
        self._refresh()
        cmd = "/usr/lib/update-notifier/apt-check"
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        stdout, stderr = proc.communicate()
        for cn in stderr.split(";"):
            if int(cn) > 0:
                log.info('Update Needed')
                return True
            log.info('No Update Needed')
        return False

    def _refresh(self):
        """
        Resynchronize the package index files from their sources
        """
        cmd = 'apt-get {} update'.format(self.base_flags)
        Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)

    def _handle(self, strat='up'):
        """
        Conbines up and dup and executes the constructed zypper command.
        """
        if strat == 'up':
            strat = 'upgrade'
        if self._updates_needed():
            base_command = ['apt-get']
            strategy_flags = ["-o Dpkg::Options::=",
                              "--allow-change-held-packages", "-fuy"]
            if self.debug:
                strategy_flags.append("--dry-run")
            base_command.extend(self.base_flags)
            base_command.extend(strat.split())
            base_command.extend(strategy_flags)
            proc = Popen(base_command, stdout=PIPE, stderr=PIPE)
            stdout, stderr = proc.communicate()
            for line in stdout:
                log.info(line)
            for line in stderr:
                log.info(line)
            log.info("returncode: {}".format(proc.returncode))
            if proc.returncode == 0:
                if os.path.isfile('/var/run/reboot-required'):
                    self.reboot_in()
            elif proc.returncode != 0:
                raise StandardError("Apt exited with non-0 returncode")
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
                100: 'ZYPPER_EXIT_INF_UPDATE_NEEDED',
                1: 'ZYPPER_EXIT_ERR_BUG',
                2: 'ZYPPER_EXIT_ERR_SYNTAX',
                3: 'ZYPPER_EXIT_ERR_INVALID_ARGS',
                4: 'ZYPPER_EXIT_ERR_ZYPP',
                5: 'ZYPPER_EXIT_ERR_PRIVILEGES',
                6: 'ZYPPER_EXIT_NO_REPOS',
                7: 'ZYPPER_EXIT_ZYPP_LOCKED',
                8: 'ZYPPER_EXIT_ERR_COMMIT'}

    VERSION = 0.1

    def __init__(self, **kwargs):
        """
        Instead of reinitializing __init__ from super,
        the child get kwargs passed as arguments to
        have the possibility to handle those differently.
        """
        self.base_command = ['zypper']
        self.zypper_flags = ['--non-interactive']
        self.kernel = kwargs.get('kernel', False)
        self.reboot = kwargs.get('reboot', True)
        self.debug = kwargs.get('debug', False)

    def _refresh(self):
        """
        Refresh Zypper before updating
        """
        log.info("Refreshing Repositories..")

        cmd = []
        strat = ["refresh"]
        cmd.extend(self.base_command)
        cmd.extend(self.zypper_flags)
        cmd.extend(strat)

        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        proc.wait()
        if proc.returncode != 0:
            log.error('Refreshing failed. Check the repos')
            log.debug('Executing {}'.format(cmd))
            return False
        

    def _updates_needed(self):
        """
        Updates that are sourced from all Repos
        """
        self._refresh()
        cmd = "zypper lu | grep -sq 'No updates found'"
        log.debug('Executing {}'.format(cmd))
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        proc.wait()
        if proc.returncode != 0:
            log.info('Update Needed')
            return True
        log.info('No Update Needed')
        return False

    def _patches_needed(self):
        """
        Updates that are sourced from an official Update
        Repository
        """

        cmd = []
        strat = ["patch-check"]
        cmd.extend(self.base_command)
        cmd.extend(self.zypper_flags)
        cmd.extend(strat)

        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        proc.wait()
        log.debug('Executing {}'.format(cmd))
        if proc.returncode == 100:
            log.info(self.RETCODES[proc.returncode])
            log.info('Patches Needed')
            return True
        log.info('No Patches Needed')
        return False

    def _handle(self, strat='up'):
        """
        Conbines up and dup and executes the constructed zypper command.
        """
        cmd = []

        if self._updates_needed():
            strategy_flags = ['--replacefiles', '--auto-agree-with-licenses']
            if self.debug:
                strategy_flags.append("--dry-run")
            if self.kernel and strat != 'dup':
                strategy_flags.append("--with-interactive")
            cmd.extend(self.base_command)
            cmd.extend(self.zypper_flags)
            cmd.extend(strat.split())
            cmd.extend(strategy_flags)
            log.debug('Executing {}'.format(cmd))
            proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
            stdout, stderr = proc.communicate()
            for line in stdout:
                log.info(line)
            for line in stderr:
                log.info(line)
            log.info("returncode: {}".format(proc.returncode))

            if int(proc.returncode) == 102:
                """
                zypper up doesn't return the necessary exitcodes.
                zypper patch does.
                zypper patch only accepts repos that are from official repos
                zypper up processes all repos.

                In a environment where you simply don't have shiny and signed repos
                like in a development environment we can't rely on a returncode
                driven rebooting.

                => Keep checks for kernel updates in /srv/salt/ceph/stage/prep.sls until
                   a better solution is found.
                """
                self.reboot_in()
            if int(proc.returncode) > 0 and int(proc.returncode) < 100:
                if int(proc.returncode) in self.RETCODES:
                    log.debug("Zypper Error: {}".format(self.RETCODES[proc.returncode]))
                log.info('Zyppers returncode < 100 indicates a failure. Check man zypper')
                raise StandardError('Zypper failed with code: {}. Look at the logs'.format(proc.returncode))
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
