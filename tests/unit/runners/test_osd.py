import pytest
from mock import patch, Mock, call
from srv.modules.runners import osd as osd_module


class TestOSDUtil():
    """
    Test OSDUtil class from runners/osd.py
    """

    @pytest.fixture(scope='class')
    def test_fix(self,
                 operation="remove",
                 force=False,
                 osd_in=True,
                 osd_out=False):
        def make_sample_data(operation=operation,
                             force=force,
                             osd_in=osd_in,
                             osd_out=osd_out):
            with patch.object(osd_module.OSDUtil, "__init__",
                              lambda x, osd_id: None):
                c = osd_module.OSDUtil('1')
                c.osd_id = '1'
                c.osd_list = ['1']
                c.host = "dummy_host"
                c.host_osds = {c.host: ['1', '2', '3', '4', '5']}
                c.osd_state = dict(_in=osd_in, out=osd_out)
                c.force = force
                c.operation = operation
                c.local = patch(
                    'salt.client.LocalClient', return_value=['foo'])
                c.local.start()
                c.local.cmd = Mock(return_value={'host': 'something'})
                return c
                c.local.stop()

        return make_sample_data

    def test_delete_grain(self, test_fix):
        test_fix = test_fix()
        test_fix._delete_grain()
        test_fix.local.cmd.assert_called_once_with(
            "dummy_host",
            "osd.delete_grain", [test_fix.osd_id],
            tgt_type='glob')

    @patch(
        'srv.modules.runners.osd.Util.master_minion',
        autospec=True,
        return_value="master_minion")
    def test_vacate_1(self, master_minion, test_fix):
        test_fix = test_fix()
        test_fix.local.cmd = Mock(return_value={'master_minion': {'1': ''}})
        result = test_fix.vacate()
        test_fix.local.cmd.assert_called_once_with(
            "master_minion",
            "osd.vacate", test_fix.osd_list,
            tgt_type='glob')
        assert result == ['1']

    @patch(
        'srv.modules.runners.osd.Util.master_minion',
        autospec=True,
        return_value="master_minion")
    def test_vacate_2(self, master_minion, test_fix):
        test_fix = test_fix()
        test_fix.local.cmd = Mock(return_value={'master_minion': {'1': 'Error'}})
        result = test_fix.vacate()
        test_fix.local.cmd.assert_called_once_with(
            "master_minion",
            "osd.vacate", test_fix.osd_list,
            tgt_type='glob')
        assert result == []

    @patch(
        'srv.modules.runners.osd.Util.master_minion',
        autospec=True,
        return_value="master_minion")
    def test_wait_loop_1(self, master_minion, test_fix):
        """
        When module returns safe-to-destroy, return successfully
        """
        test_fix = test_fix()
        test_fix.osd_id = 0
        test_fix.retries = 1
        test_fix.local.cmd = Mock(return_value={'master_minion': 'osd.0 is safe to destroy'})
        ret = test_fix._wait_until_empty()
        assert ret is True

    @patch(
        'srv.modules.runners.osd.Util.master_minion',
        autospec=True,
        return_value="master_minion")
    def test_wait_loop_2(self, master_minion, test_fix):
        """
        When retries are exhausted, fail
        """
        test_fix = test_fix()
        test_fix.osd_id = 0
        test_fix.retries = 1
        test_fix.local.cmd = Mock(return_value={'master_minion': 'Timeout expired - osd.0 has 181 PGs remaining'})
        ret = test_fix._wait_until_empty()
        assert ret is False


    @patch('srv.modules.runners.osd.OSDUtil._mark_osd', autospec=True)
    @patch(
        'srv.modules.runners.osd.Util.master_minion',
        autospec=True,
        return_value="master_minion")
    def test_recover_osd_state_in(self, master_minion, mark_osd_mock,
                                  test_fix):
        test_fix = test_fix()
        test_fix.recover_osd_state()
        test_fix._mark_osd.assert_called_once_with(test_fix, 'in')

    @patch('srv.modules.runners.osd.OSDUtil._mark_osd', autospec=True)
    @patch(
        'srv.modules.runners.osd.Util.master_minion',
        autospec=True,
        return_value="master_minion")
    def test_recover_osd_state_out(self, master_minion, mark_osd_mock,
                                   test_fix):
        test_fix = test_fix(osd_out=True, osd_in=False)
        test_fix.recover_osd_state()
        test_fix._mark_osd.assert_called_once_with(test_fix, 'out')

    @pytest.mark.skip(
        reason=
        "That function will be simplified in the future. Ceph is improving on this in soon"
    )
    def test_get_osd_state(self, test_fix):
        pass

    def test_lvm_zap(self, test_fix):
        test_fix = test_fix()
        test_fix.local.cmd.return_value = {
            'node': 'Zapping successful for OSD'
        }
        test_fix._lvm_zap()

        test_fix.local.cmd.assert_called_once_with(
            "dummy_host",
            'cmd.run', [
                'ceph-volume lvm zap --osd-id {} --destroy'.format(
                    test_fix.osd_id)
            ],
            tgt_type='glob')

    def test_lvm_zap_fail(self, test_fix):
        test_fix = test_fix()
        test_fix.local.cmd.return_value = {'node': 'Nope, some error'}
        with pytest.raises(RuntimeError):
            test_fix._lvm_zap()

    def test_try_simple_zap(self, test_fix):
        test_fix = test_fix()
        def cmds_side_effect(*args, **kwargs):
            assert len(args) == 3
            assert args[0] == "dummy_host"
            assert args[1] == "cmd.run"
            cmd_run_args = args[2]
            assert len(cmd_run_args) == 1
            cmd_run = cmd_run_args[0]

            if cmd_run.endswith('xargs lsblk -no PKNAME | uniq'):
                return { 'node': 'vdb\nvdc\nvdd' }
            elif cmd_run.endswith('ceph-volume lvm zap --destroy'):
                return { 'node': 'Zapping successful for OSD {}'.format(test_fix.osd_id) }
            elif cmd_run.endswith('[1-9] /proc/partitions'):
                return { 'node': '2' }
            elif 'grep -c' in cmd_run:
                return { 'node': '2' }
        test_fix.local.cmd.side_effect = cmds_side_effect
        assert test_fix._try_simple_zap() == True
        expected_calls = [
                            call("dummy_host",
                                 "cmd.run", 
                                 [ ("cat /etc/ceph/osd/{}-*.json | "
                                             "jq '.block.path,.data.path,"
                                             ".[\"block.db\"].path,.[\"block.wal\"].path' | "
                                             "xargs -r readlink -e | "
                                             "xargs lsblk -no PKNAME | "
                                             "uniq").format(test_fix.osd_id)
                                 ],
                                 tgt_type='glob'
                                ),
                            call("dummy_host",
                                 "cmd.run", 
                                 [ ("cat /etc/ceph/osd/{}-*.json | "
                                             "jq '.block.path,.data.path,"
                                             ".[\"block.db\"].path,.[\"block.wal\"].path' | "
                                             "xargs -r readlink -e | "
                                             "xargs ceph-volume lvm zap --destroy").format(test_fix.osd_id)
                                 ],
                                 tgt_type='glob'
                                ),
                            call("dummy_host",
                                 "cmd.run", [ ("grep -c vdb[1-9] /proc/partitions") ],
                                 tgt_type='glob'),
                            call("dummy_host",
                                 "cmd.run", [ ("grep -c vdc[1-9] /proc/partitions") ],
                                 tgt_type='glob'),
                            call("dummy_host",
                                 "cmd.run", [ ("grep -c vdd[1-9] /proc/partitions") ],
                                 tgt_type='glob')
                         ]
        assert expected_calls == test_fix.local.cmd.mock_calls

    def test_try_simple_zap_zaps_1_parent_disk(self, test_fix):
        test_fix = test_fix()
        def cmds_side_effect(*args, **kwargs):
            assert len(args) == 3
            assert args[0] == "dummy_host"
            assert args[1] == "cmd.run"
            cmd_run_args = args[2]
            assert len(cmd_run_args) == 1
            cmd_run = cmd_run_args[0]

            if cmd_run.endswith('xargs lsblk -no PKNAME | uniq'):
                return { 'node': 'vdb\nvdc\nvdd' }
            elif cmd_run.endswith('ceph-volume lvm zap --destroy'):
                return { 'node': 'Zapping successful for OSD {}'.format(test_fix.osd_id) }
            elif cmd_run.endswith('vdb[1-9] /proc/partitions'):
                return { 'node': '2' }
            elif cmd_run.endswith('vdc[1-9] /proc/partitions'):
                return { 'node': '0' }
            elif cmd_run.endswith('vdd[1-9] /proc/partitions'):
                return { 'node': '2' }
            elif 'grep -c' in cmd_run:
                return { 'node': '2' }
            elif cmd_run.endswith('--destroy /dev/vdc'):
                return { 'node': 'Zapping successful ' }
        test_fix.local.cmd.side_effect = cmds_side_effect
        assert test_fix._try_simple_zap() == True
        expected_calls = [
                            call("dummy_host",
                                 "cmd.run", 
                                 [ ("cat /etc/ceph/osd/{}-*.json | "
                                             "jq '.block.path,.data.path,"
                                             ".[\"block.db\"].path,.[\"block.wal\"].path' | "
                                             "xargs -r readlink -e | "
                                             "xargs lsblk -no PKNAME | "
                                             "uniq").format(test_fix.osd_id)
                                 ],
                                 tgt_type='glob'
                                ),
                            call("dummy_host",
                                 "cmd.run", 
                                 [ ("cat /etc/ceph/osd/{}-*.json | "
                                             "jq '.block.path,.data.path,"
                                             ".[\"block.db\"].path,.[\"block.wal\"].path' | "
                                             "xargs -r readlink -e | "
                                             "xargs ceph-volume lvm zap --destroy").format(test_fix.osd_id)
                                 ],
                                 tgt_type='glob'
                                ),
                            call("dummy_host",
                                 "cmd.run", [ ("grep -c vdb[1-9] /proc/partitions") ],
                                 tgt_type='glob'),
                            call("dummy_host",
                                 "cmd.run", [ ("grep -c vdc[1-9] /proc/partitions") ],
                                 tgt_type='glob'),
                            call("dummy_host",
                                 "cmd.run", [ ("ceph-volume lvm zap --destroy /dev/vdc") ],
                                 tgt_type='glob'),
                            call("dummy_host",
                                 "cmd.run", [ ("grep -c vdd[1-9] /proc/partitions") ],
                                 tgt_type='glob')
                         ]
        assert expected_calls == test_fix.local.cmd.mock_calls

    def test_try_simple_zap_error_zap_parent_disk(self, test_fix):
        test_fix = test_fix()
        def cmds_side_effect(*args, **kwargs):
            assert len(args) == 3
            assert args[0] == "dummy_host"
            assert args[1] == "cmd.run"
            cmd_run_args = args[2]
            assert len(cmd_run_args) == 1
            cmd_run = cmd_run_args[0]

            if cmd_run.endswith('xargs lsblk -no PKNAME | uniq'):
                return { 'node': 'vdb\nvdc\nvdd' }
            elif cmd_run.endswith('ceph-volume lvm zap --destroy'):
                return { 'node': 'Zapping successful for OSD {}'.format(test_fix.osd_id) }
            elif cmd_run.endswith('vdb[1-9] /proc/partitions'):
                return { 'node': '2' }
            elif cmd_run.endswith('vdc[1-9] /proc/partitions'):
                return { 'node': '0' }
            elif cmd_run.endswith('vdd[1-9] /proc/partitions'):
                return { 'node': '2' }
            elif 'grep -c' in cmd_run:
                return { 'node': '2' }
            elif cmd_run.endswith('--destroy /dev/vdc'):
                return { 'node': 'Some error' }
        test_fix.local.cmd.side_effect = cmds_side_effect
        assert test_fix._try_simple_zap() == False
        expected_calls = [
                            call("dummy_host",
                                 "cmd.run", 
                                 [ ("cat /etc/ceph/osd/{}-*.json | "
                                             "jq '.block.path,.data.path,"
                                             ".[\"block.db\"].path,.[\"block.wal\"].path' | "
                                             "xargs -r readlink -e | "
                                             "xargs lsblk -no PKNAME | "
                                             "uniq").format(test_fix.osd_id)
                                 ],
                                 tgt_type='glob'
                                ),
                            call("dummy_host",
                                 "cmd.run", 
                                 [ ("cat /etc/ceph/osd/{}-*.json | "
                                             "jq '.block.path,.data.path,"
                                             ".[\"block.db\"].path,.[\"block.wal\"].path' | "
                                             "xargs -r readlink -e | "
                                             "xargs ceph-volume lvm zap --destroy").format(test_fix.osd_id)
                                 ],
                                 tgt_type='glob'
                                ),
                            call("dummy_host",
                                 "cmd.run", [ ("grep -c vdb[1-9] /proc/partitions") ],
                                 tgt_type='glob'),
                            call("dummy_host",
                                 "cmd.run", [ ("grep -c vdc[1-9] /proc/partitions") ],
                                 tgt_type='glob'),
                            call("dummy_host",
                                 "cmd.run", [ ("ceph-volume lvm zap --destroy /dev/vdc") ],
                                 tgt_type='glob'),
                            call("dummy_host",
                                 "cmd.run", [ ("grep -c vdd[1-9] /proc/partitions") ],
                                 tgt_type='glob')
                         ]
        assert expected_calls == test_fix.local.cmd.mock_calls

    @patch('srv.modules.runners.osd.OSDUtil._try_simple_zap', autospec=True)
    def test_lvm_zap_fail_calls_try_simple_zap(self, try_simple_zap, test_fix):
        test_fix = test_fix()
        test_fix.local.cmd.return_value = {'node': 'Nope, some error'}

        test_fix._lvm_zap()
        test_fix._try_simple_zap.assert_called_once_with(test_fix)

    @patch(
        'srv.modules.runners.osd.Util.master_minion',
        autospec=True,
        return_value="master_minion")
    def test_mark_destroyed(self, master_minion, test_fix):
        test_fix = test_fix()
        test_fix.local.cmd.return_value = {'node': 'destroyed osd'}
        test_fix._mark_destroyed()

        test_fix.local.cmd.assert_called_once_with(
            "master_minion",
            'cmd.run', [
                'ceph osd destroy {} --yes-i-really-mean-it'.format(
                    test_fix.osd_id)
            ],
            tgt_type='glob')

    @patch(
        'srv.modules.runners.osd.Util.master_minion',
        autospec=True,
        return_value="master_minion")
    def test_mark_destroyed_fail(self, master_minion, test_fix):
        test_fix = test_fix()
        test_fix.local.cmd.return_value = {'node': 'Nope, some error'}
        with pytest.raises(RuntimeError):
            test_fix._mark_destroyed()

    @patch(
        'srv.modules.runners.osd.Util.master_minion',
        autospec=True,
        return_value="master_minion")
    def test_purge_osd(self, master_minion, test_fix):
        test_fix = test_fix()
        test_fix.local.cmd.return_value = {'node': 'purged osd'}
        test_fix._purge_osd()

        test_fix.local.cmd.assert_called_once_with(
            "master_minion",
            'cmd.run', [
                'ceph osd purge {} --yes-i-really-mean-it'.format(
                    test_fix.osd_id)
            ],
            tgt_type='glob')

    @patch(
        'srv.modules.runners.osd.Util.master_minion',
        autospec=True,
        return_value="master_minion")
    def test_purge_osd_fail(self, master_minion, test_fix):
        test_fix = test_fix()
        test_fix.local.cmd.return_value = {'node': 'Nope, some error'}
        with pytest.raises(RuntimeError):
            test_fix._purge_osd()

    @pytest.mark.parametrize("action", ['start', 'stop', 'enable', 'disable'])
    def test_service(self, action, test_fix):
        test_fix = test_fix()
        test_fix.local.cmd.return_value = {'node': 'Something'}
        test_fix._service(action)

        test_fix.local.cmd.assert_called_once_with(
            "dummy_host",
            'service.{}'.format(action),
            ['ceph-osd@{}'.format(test_fix.osd_id)],
            tgt_type='glob')

    @pytest.mark.parametrize("state", ['out', 'down'])
    @patch(
        'srv.modules.runners.osd.Util.master_minion',
        autospec=True,
        return_value="master_minion")
    def test_mark_osd(self, master_minion, state, test_fix):
        test_fix = test_fix()
        test_fix.local.cmd.return_value = {'node': 'marked'}
        ret = test_fix._mark_osd(state)

        test_fix.local.cmd.assert_called_once_with(
            "master_minion",
            'cmd.run', ['ceph osd {} {}'.format(state, test_fix.osd_id)],
            tgt_type='glob')

        assert ret is True

    @pytest.mark.parametrize("state", ['out', 'down'])
    @patch(
        'srv.modules.runners.osd.Util.master_minion',
        autospec=True,
        return_value="master_minion")
    def test_mark_osd_is_already(self, master_minion, state, test_fix):
        test_fix = test_fix()
        test_fix.local.cmd.return_value = {
            'node': 'osd.{} is already {}'.format(test_fix.osd_id, state)
        }
        test_fix._mark_osd(state)

        test_fix.local.cmd.assert_called_once_with(
            "master_minion",
            'cmd.run', ['ceph osd {} {}'.format(state, test_fix.osd_id)],
            tgt_type='glob')

    @pytest.mark.parametrize("state", ['out', 'down'])
    @patch(
        'srv.modules.runners.osd.Util.master_minion',
        autospec=True,
        return_value="master_minion")
    def test_mark_osd_is_does_not_exist(self, master_minion, state, test_fix):
        test_fix = test_fix()
        test_fix.local.cmd.return_value = {
            'node': 'osd.{} does not exist'.format(test_fix.osd_id)
        }
        with pytest.raises(osd_module.OSDNotFound):
            test_fix._mark_osd(state)

    @pytest.mark.parametrize("state", ['out', 'down'])
    @patch(
        'srv.modules.runners.osd.Util.master_minion',
        autospec=True,
        return_value="master_minion")
    def test_mark_osd_state_unknown(self, master_minion, state, test_fix):
        test_fix = test_fix()
        test_fix.local.cmd.return_value = {
            'node': 'osd.{} bogus bogus'.format(test_fix.osd_id)
        }
        with pytest.raises(osd_module.OSDUnknownState):
            test_fix._mark_osd(state)

    def test_find_host(self, test_fix):
        test_fix = test_fix()
        ret = test_fix._find_host()
        assert ret == test_fix.host

    def test_find_host_osd_not_in_host(self, test_fix):
        """ In this example we only have one host with OSDs 1..5
        Monkeypatch osd_id to 6 in order to simulate the second branch
        Expect to return ""
        """
        test_fix = test_fix()
        test_fix.osd_id = '6'
        ret = test_fix._find_host()
        assert ret == ""

    @patch('srv.modules.runners.osd.Util.local.cmd')
    def test_host_osds(self, local, test_fix):
        test_fix = test_fix()
        test_fix._host_osds()
        local.assert_called_once_with(
            'I@roles:storage', 'osd.list', tgt_type='compound')

    @patch(
        'srv.modules.runners.osd.Util.master_minion',
        autospec=True,
        return_value="master_minion")
    @patch('salt.client.LocalClient', autospec=True)
    def test_ok_to_stop(self, local, master_minion):
        local.return_value.cmd.return_value = {
            'dummy_host': 'are ok to stop without reducing availability'
        }
        ret = osd_module.ok_to_stop_osds("1 2")
        assert ret is True

    @patch(
        'srv.modules.runners.osd.Util.master_minion',
        autospec=True,
        return_value="master_minion")
    @patch('salt.client.LocalClient', autospec=True)
    def test_not_ok_to_stop(self, local, master_minion):
        local.return_value.cmd.return_value = {
            'dummy_host':
            'are NOTNOTNOT ok to stop without reducing availability'
        }
        with pytest.raises(osd_module.NotOkToStop):
            osd_module.ok_to_stop_osds("1 2")

    @patch(
        'srv.modules.runners.osd.ok_to_stop_osds',
        autospec=True,
        return_value=True)
    def test_pre_check_force(self, ok_to_stop):
        osd_module.pre_check("1, 2", True)
        assert ok_to_stop.called is False

    @patch(
        'srv.modules.runners.osd.ok_to_stop_osds',
        autospec=True,
        return_value=True)
    def test_pre_check_no_force(self, ok_to_stop):
        osd_module.pre_check("1, 2", False)
        assert ok_to_stop.called is True

    @patch(
        'srv.modules.runners.osd.Util.get_osd_list_for',
        return_value={'': []})
    def test__target_lookup(self, local):
        ret = osd_module._target_lookup("")
        assert ret == []

    def test__target_lookup_empty(self):
        ret = osd_module._target_lookup(tuple([]))
        assert ret == []

    @patch(
        'srv.modules.runners.osd.Util.get_osd_list_for',
        return_value={'foo': [1, 2, 3, 4, 5, 6]})
    def test__target_lookup_compound(self, local):
        ret = osd_module._target_lookup(tuple(["dummy_target"]))
        assert ret == [1, 2, 3, 4, 5, 6]

    def test__target_lookup_list(self):
        ret = osd_module._target_lookup(tuple([1, 2, 3]))
        assert ret == [1, 2, 3]
