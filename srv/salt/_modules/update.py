from subprocess import Popen, PIPE
import logging

log = logging.getLogger(__name__)
RETCODES = {102: 'ZYPPER_EXIT_INF_REBOOT_NEEDED'}


class ZypperUpdate(object):

    def __init__(self, **kwargs):
        self.dist_upgrade = kwargs.get('dup', False)
        self.debug = kwargs.get('debug', False)

    def _is_needed(self):
        cmd = "zypper lu | grep -sq 'No updates found'"
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        proc.wait()
        if proc.returncode != 0:
            log.info('Update Needed')
            return True
        else:
            log.info('No Update Needed')
            return False

    def updup(self):
        if self.debug:
            log.warning('THIS MODULE WAS EXECUTED')
            log.debug('THIS MODULE WAS EXECUTED')
            log.info('THIS MODULE WAS EXECUTED')
        if self._is_needed():
            strategy = 'update'
            if self.dist_upgrade:
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
                log.info('reboot required')
            if proc.returncode <= 100:
                log.info('error occured')
        else:
            log.warn('NO UPDATES NEEDED')
            log.info('NO UPDATES NEEDED')
            log.debug('NO UPDATES NEEDED')


def zypper_up(**kwargs):
    zu = ZypperUpdate(**kwargs)
    zu.updup()
