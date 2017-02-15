from subprocess import Popen, PIPE
import logging

log = logging.getLogger(__name__)
VERSION = 0.1
RETCODES = {102: 'ZYPPER_EXIT_INF_REBOOT_NEEDED'}


class Zypper(object):

    def __init__(self, **kwargs):
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
        self.debug = kwargs.get('debug', False)
        self.kernel = kwargs.get('kernel', False)

    def _is_needed(self):
        cmd = "zypper lu | grep -sq 'No updates found'"
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        proc.wait()
        if proc.returncode != 0:
            log.info('Update Needed')
        else:
            log.info('No Update Needed')

    def reboot(self):
        cmd = "shutdown -r now"
        proc = Popen(cmd.split(), stdout=PIPE)

    def _handle(self, strat='up'):
        log.debug("zypper module v{} was executed".format(VERSION))
        if self._is_needed():
            if strat == 'dup' or strat == 'dist-upgrade':
                strategy = 'dist-upgrade'
            cmd = "zypper --non-interactive {} --replacefiles --auto-agree-with-licenses".format(strategy)
            proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
            proc.wait()
            for line in proc.stdout:
                log.info(line)
            for line in proc.stderr:
                log.info(line)
            log.info("returncode: {}".format(proc.returncode))

            if proc.returncode == 102:
                log.info(RETCODES[proc.returncode])
                log.info('Reboot required')
                self.reboot
            if proc.returncode <= 100:
                log.info('Error occured')
                raise StandardError('Zypper failed. Look in the logs')
        else:
            log.info('System up to date')

def up(**kwargs):
    zu = Zypper(**kwargs)
    zu._handle(strat='up')

def dup(**kwargs):
    zu = Zypper(**kwargs)
    zu._handle(strat='dup')
