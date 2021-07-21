#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Runner to remove and replace osds
"""

from __future__ import absolute_import
from __future__ import print_function
import json
# pylint: disable=import-error,3rd-party-module-not-gated,redefined-builtin
import salt.client
import salt.runner
from salt.ext.six.moves import map
import tee


log = tee.console(__name__)


def help_():
    """
    Usage
    """
    usage = ('salt-run remove.osd id [id ...][force=True]:\n\n'
             '    Removes an OSD\n'
             '\n\n')
    print(usage)
    return ""


class OSDNotFound(Exception):
    """ RuntimeError to raise when the OSD was not found in the cluster """
    pass


class OSDUnknownState(Exception):
    """ RuntimeError to raise when an unknown state was found for a OSD """
    pass


class NotOkToStop(Exception):
    """ RuntimeError to raise when removing OSDs would result in a degraded/unavailable state"""
    pass


class Util(object):
    """
    Util helper class
    """

    local = salt.client.LocalClient()

    @staticmethod
    def join_list(inp):
        """ Join a list of integers to a list of strings """
        return " ".join([str(x) for x in list(inp)])

    @classmethod
    def get_osd_list_for(cls, target):
        """ call salt's LocalClient for osd.list with target """
        return cls.local.cmd(target, "osd.list", tgt_type="compound")

    @staticmethod
    def master_minion():
        """
        Load the master modules
        """
        __master_opts__ = salt.config.client_config("/etc/salt/master")
        __master_utils__ = salt.loader.utils(__master_opts__)
        __salt_master__ = salt.loader.minion_mods(
            __master_opts__, utils=__master_utils__)

        return __salt_master__["master.minion"]()

    def find_by_osd_id(self, target: str, osd_id: int) -> dict:
        """ Find by osd_id and return details about disk """
        osd_metadata: dict = self.local.cmd(
            target, 'cephdisks.find_by_osd_id', [osd_id],
            tgt_type="compound")[target]
        if isinstance(osd_metadata, str):
            if osd_metadata.startswith(
                    'The minion function caused an exception'):
                log.error(osd_metadata)
                return dict()
        if isinstance(osd_metadata, list) and osd_metadata:
            return osd_metadata[0]
        return dict()


class OSDUtil(Util):
    """ Util class for OSD handling """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, *args, **kwargs):
        Util.__init__(self)
        self.osd_id = int(args[0])
        self.osd_list = args
        self.local = Util.local
        self.host_osds = self._host_osds()
        self.host = self._find_host()
        self.osd_state = self._get_osd_state()
        self.force: bool = kwargs.get('force', False)
        self.operation: str = kwargs.get('operation', 'None')
        self.retries: int = kwargs.get('retries', 60)  # ~1 hour
        self.osd_metadata = self.get_osd_metadata()

    def vacate(self):
        """ Remote call to osd.py to set the weight to zero"""
        osds = f", ".join(map(str, self.osd_list))
        if self.force:
            log.warning(f"Not emptying OSD {osds}")
            return self.osd_list

        print(f"Emptying osd {osds}")
        ret = self.local.cmd(
            Util.master_minion(),
            'osd.vacate',
            self.osd_list,
            tgt_type="glob")
        results = ret[Util.master_minion()]

        osd_list = []
        for osd_id in results:
            if results[osd_id] == "":
                osd_list.append(osd_id)
            else:
                log.error(f"Skipping OSD {osd_id}: {results[osd_id]}")
        return osd_list

    def restore_weights(self):
        """ Remote call to osd.py to set the weight to zero"""
        osds = f", ".join(map(str, self.osd_list))

        print(f"Restoring weights of osd {osds}")
        ret = self.local.cmd(
            Util.master_minion(),
            'osd.restore_weights',
            self.osd_list,
            tgt_type="glob")
        results = ret[Util.master_minion()]

        for osd_id in results:
            if results[osd_id] is not True:
                log.error(f"OSD {osd_id}: {results[osd_id]}")
        return ""

    def get_osd_metadata(self) -> dict:
        """ Get metadata for OSD """
        if self.host and self.osd_id:
            return self.find_by_osd_id(self.host, self.osd_id)
        return dict()

    @property
    def path_for_osd(self) -> str:
        """ Retrieve path for OSD """
        return self.osd_metadata.get('path', 'n/a')

    @property
    def model_for_osd(self) -> str:
        """ Retrieve model for OSD """
        return self.osd_metadata.get('sys_api', dict()).get('model', 'n/a')

    def serial_for_osd(self) -> str:
        """ Not implemented """
        pass

    def replace(self):
        """
        1) ceph osd out $id
        2) systemctl stop ceph-osd@$id (maybe do more see osd.py (terminate()))
        2.1) also maybe wait if not force
        3) ceph osd destroy $id --yes-i-really-mean-it
        4) ceph-volume lvm zap --osd-id $id
        """
        log.info("Preparing replacement of osd {} on host {}".format(
            self.osd_id, self.host))
        return self._call()

    def remove(self):
        """
        1) Call 'ceph osd out $id'
        2) Call systemctl stop ceph-osd@$id (on minion)
        3) ceph osd purge $id --yes-i-really-mean-it
        3.1) (slide-in) remove the grain from the 'ceph:' struct
        4) call ceph-volume lvm zap --osd-id $id --destroy (on minion)
        5) zap doesn't destroy the partition -> find the associated partitions and
           call `ceph-volume lvm zap <device>` (optional)
        """
        log.info("Removing osd {} on host {}".format(self.osd_id, self.host))
        return self._call()

    # pylint: disable=too-many-return-statements
    def _call(self):
        """
        Make the necessary calls based on the context
        context -> remove || replace
        """

        if not self.host:
            log.error("No host found")
            return False

        if not self.force:
            log.info("Checking if OSD can be destroyed")
            if self._wait_until_empty() is False:
                return False
        try:
            self._mark_osd('out')
        except OSDNotFound:
            return False
        except OSDUnknownState:
            log.info("Attempting rollback to previous state")
            self.recover_osd_state()
            return False

        try:
            self._service('disable')
            self._service('stop')
            self._mark_osd('down')
            # The original implementation
            # pkilled (& -9 -f'd ) the osd-process
            # including a double check with pgrep
            # considering to add that again
        except RuntimeError:
            log.error("Encoutered issue while operating on systemd service")
            log.warning("Attempting rollback to previous state")
            self.recover_osd_state()
            self._service('enable')
            self._service('start')
            return False

        try:
            if self.operation == 'remove':
                log.info("Purging from the crushmap")
                self._purge_osd()
            elif self.operation == 'replace':
                log.info("Marking OSD 'destroyed'")
                self._mark_destroyed()
            else:
                raise RuntimeError("Unknown operation: {}".format(
                    self.operation))
        except RuntimeError:
            log.error("Encoutered issue while purging osd")
            log.warning("Attempting rollback to previous state")
            self.recover_osd_state()
            self._service('enable')
            self._service('start')
            return False

        try:
            self._delete_grain()
        except RuntimeError:
            log.error("Encoutered issue while zapping the disk")
            log.warning("No rollback possible at this stage")
            return False

        try:
            print("Zapping the device")
            self._lvm_zap()
            print("\n")
        except RuntimeError:
            log.error("Encoutered issue while zapping the disk")
            log.warning("No rollback possible at this stage")
            return False

        return True

    def _delete_grain(self):
        """ Delete grains after removing an OSD (if grain is still present) """
        log.debug("Deleting grain for osd {}".format(self.osd_id))
        self.local.cmd(
            self.host, 'osd.delete_grain', [self.osd_id], tgt_type="glob")
        # There is no handling of returncodes in delete_grain whatsoever..
        # No point in checking messages
        return True

    def _wait_until_empty(self):
        """ Wait for roughly an hour until the osd is empty"""
        print("Waiting for ceph to catch up.")
        counter = 0
        while counter < self.retries:
            if counter > 0:
                log.info("Retrying...")
            log.info("Waiting for osd {} to empty".format(self.osd_id))
            ret = self.local.cmd(
                Util.master_minion(),
                'osd.wait_until_empty', [self.osd_id],
                tgt_type="glob")
            message = list(ret.values())[0]
            log.info(message)
            if message.startswith("osd.{} is safe to destroy".format(
                    self.osd_id)):
                return True
            counter += 1
        return False

    def recover_osd_state(self):
        """ Wrapper method to recover the previous osd_state after a rollback """
        if self.osd_state:
            if self.osd_state.get('_in', False):
                self._mark_osd('in')
            if self.osd_state.get('out', False):
                self._mark_osd('out')

    def _get_osd_state(self):
        """ Method to get the current osd_state """
        cmd = 'ceph osd dump --format=json'
        log.debug("Executing: {}".format(cmd))
        ret = self.local.cmd(
            Util.master_minion(), "cmd.run", [cmd], tgt_type="glob")
        message = list(ret.values())[0]
        message_json = json.loads(message)
        all_osds = message_json.get('osds', [])
        try:
            osd_info = [
                x for x in all_osds if x.get('osd', '') == self.osd_id
            ][0]
        except IndexError:
            raise OSDNotFound("OSD {} doesn't exist in the cluster".format(
                self.osd_id))
        return dict(
            _in=bool(osd_info.get('in', 0)), out=bool(osd_info.get('out', 0)))

    def _lvm_zap(self):
        """ Remote call to minion for lvm zap """
        # ceph-volume is capable of zapping non-c-v disks, but can't determine
        # the linked drives properly
        # osd-node2:~ # ceph-volume lvm zap --osd-id 8
        # -->  RuntimeError: Unable to find any LV for zapping OSD: 8
        # calling the /device however is fine.
        # That means we have to find devices by osd_id first

        cmd = 'ceph-volume lvm zap --osd-id {} --destroy'.format(self.osd_id)
        log.debug("Executing: {}".format(cmd))
        ret = self.local.cmd(self.host, "cmd.run", [cmd], tgt_type="glob")
        message = list(ret.values())[0]
        if 'Zapping successful for OSD' not in message:
            log.info("Zapping by osd_id failed, attempting to zap devices "
                     "listed in /etc/ceph/osd/{}.*.json".format(self.osd_id))
            self._try_simple_zap()
        return True

    def _try_simple_zap(self):
        """
        Remote call to minion to zap devices listed by c-v simple scan output
        """
        simple_scan_json = 'cat /etc/ceph/osd/{}-*.json'.format(self.osd_id)
        cmd = simple_scan_json + (' | jq \'.block.path,.data.path,'
                                  '.["block.db"].path,.["block.wal"].path\''
                                  ' | xargs -r readlink -e '
                                  '| xargs ceph-volume lvm zap --destroy')
        log.debug("Executing: {}".format(cmd))
        ret = self.local.cmd(self.host, "cmd.run", [cmd], tgt_type="glob")
        message = list(ret.values())[0]
        if 'Zapping successful for' not in message:
            log.error("Zapping the osd failed: {}".format(message))
            raise RuntimeError
        return True

    def _mark_destroyed(self):
        """ Mark an osd destroyed """
        cmd = "ceph osd destroy {} --yes-i-really-mean-it".format(self.osd_id)
        log.debug("Executing: {}".format(cmd))
        ret = self.local.cmd(
            Util.master_minion(),
            "cmd.run",
            [cmd],
            tgt_type="glob",
        )
        message = list(ret.values())[0]

        if not message.startswith('destroyed osd'):
            log.error("Destroying the osd failed: {}".format(message))
            raise RuntimeError
        return True

    def _purge_osd(self):
        """ Purge an osd """
        cmd = "ceph osd purge {} --yes-i-really-mean-it".format(self.osd_id)
        log.debug("Executing: {}".format(cmd))
        ret = self.local.cmd(
            Util.master_minion(),
            "cmd.run",
            [cmd],
            tgt_type="glob",
        )
        message = list(ret.values())[0]
        if not message.startswith('purged osd'):
            log.error("Purging the osd failed: {}".format(message))
            raise RuntimeError
        return True

    def _service(self, action):
        """ Wrapper to start/stop a systemd unit """
        log.debug("Calling service.{} on {}".format(action, self.osd_id))
        ret = self.local.cmd(
            self.host,
            'service.{}'.format(action), ['ceph-osd@{}'.format(self.osd_id)],
            tgt_type="glob")
        message = list(ret.values())[0]
        if not message:
            log.error("{}ing the systemd service resulted with {}".format(
                action.capitalize(), message))
            raise RuntimeError
        return True

    def _mark_osd(self, state):
        """ Mark a osd out/in """
        cmd = "ceph osd {} {}".format(state, self.osd_id)
        log.debug("Running command {}".format(cmd))
        ret = self.local.cmd(
            Util.master_minion(),
            "cmd.run",
            [cmd],
            tgt_type="glob",
        )
        message = list(ret.values())[0]
        if message.startswith('marked'):
            log.debug("Marking osd {} - {} -".format(self.osd_id, state))
        elif message.startswith('osd.{} is already {}'.format(
                self.osd_id, state)):
            log.info(message)
        elif message.startswith('osd.{} does not exist'.format(self.osd_id)):
            log.error(message)
            raise OSDNotFound
        else:
            log.warning("OSD not in expected state. {}".format(message))
            raise OSDUnknownState
        return True

    def _find_host(self):
        """
        Search lists for ID, return host
        """
        for host in self.host_osds:
            if str(self.osd_id) in self.host_osds.get(host):
                return host
        return ""

    @staticmethod
    def _host_osds():
        """
        osd.list is a mix of 'mounts' and 'grains'
        in the future this should come from ceph-volume inventory
        - check
        """
        return Util.get_osd_list_for("I@roles:storage")


def ok_to_stop_osds(osd_list):
    """ Ask ceph is all given osds are ok-to-stop """
    cmd = "ceph osd ok-to-stop {}".format(osd_list)
    log.info("Running command {}".format(cmd))
    local = salt.client.LocalClient()
    ret = local.cmd(
        Util.master_minion(),
        "cmd.run",
        [cmd],
        tgt_type="glob",
    )
    message = list(ret.values())[0]
    try:
        # ceph 14.2.22 gives something like:
        # {"ok_to_stop":true,"osds":[0],"num_ok_pgs":98,"num_not_ok_pgs":0,"ok_become_degraded": [...]}
        ok_to_stop = json.loads(message)
        if ok_to_stop['ok_to_stop']:
            return True
    except ValueError:
        # `ceph osd ok-to-stop` output isn't parseable JSON, fall back to
        # checking the status string we'd expect from ceph < v14.2.22
        if 'are ok to stop without reducing availability' in message:
            return True
    print("You are about to remove OSD(s) that would result in degraded PGs. Stopping")
    raise NotOkToStop(message)


def pre_check(osd_list, force):
    """ Pre check method
    Skip if force flag is set
    """
    osd_list = Util.join_list(osd_list)
    if force:
        print("The 'force' flag is set. ok-to-stop checks are disabled."
              " Please use with caution.")
    else:
        ok_to_stop_osds(osd_list)


def _target_lookup(inp):
    """
    This allows to specify a compound target on the command line
    """
    osd_list = []
    for target in inp:
        if isinstance(target, int):
            # It's safe to assume that when the first arg is
            # an integer we get a list of osd_ids
            return list(inp)
        elif isinstance(target, str):
            print("Detected a compound target")
            osd_list_return = Util.get_osd_list_for(target)

            if not osd_list_return:
                print("Target: {} did not match anything".format(target))
                return False
            for _, osds in osd_list_return.items():
                if osds:
                    osd_list.extend(osds)
            print("Found OSDS: {} in compound target {}".format(
                osd_list, target))
    return osd_list


def remove(*args, **kwargs):
    """ User facing osd.remove function """
    results = dict()
    kwargs.update({'operation': 'remove'})
    osd_list = _target_lookup(args)
    if not osd_list:
        return False
    pre_check(osd_list, kwargs.get('force', False))
    osd_list = OSDUtil(*osd_list, **kwargs).vacate()
    for osd_id in osd_list:
        osd_obj = OSDUtil(osd_id, **kwargs)
        _rc = osd_obj.remove()
        results.update({
            str(osd_id): {
                'returncode': _rc,
                'path': osd_obj.path_for_osd,
                'model': osd_obj.model_for_osd
            }
        })
    return results


def replace(*args, **kwargs):
    """ User facing osd.replace function """
    results = dict()
    kwargs.update({'operation': 'replace'})
    osd_list = _target_lookup(args)
    if not osd_list:
        return False
    pre_check(osd_list, kwargs.get('force', False))
    osd_list = OSDUtil(*osd_list, **kwargs).vacate()
    for osd_id in osd_list:
        osd_obj = OSDUtil(osd_id, **kwargs)
        _rc = osd_obj.replace()
        results.update({
            str(osd_id): {
                'returncode': _rc,
                'path': osd_obj.path_for_osd,
                'model': osd_obj.model_for_osd
            }
        })
    osd_list = OSDUtil(*osd_list, **kwargs).restore_weights()
    return results


__func_alias__ = {
    'help_': 'help',
}
