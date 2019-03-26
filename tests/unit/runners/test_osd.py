import pytest
from mock import patch, Mock
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
                c.host = "dummy_host"
                c.host_osds = {c.host: ['1', '2', '3', '4', '5']}
                c.osd_state = dict(_in=osd_in, out=osd_out)
                c.force = force
                c.operation = operation
                c.local = patch(
                    'salt.client.LocalClient', return_value=['moo'])
                c.local.start()
                c.local.cmd = Mock(return_value={'host': 'something'})
                return c
                c.local.stop()

        return make_sample_data

    @pytest.mark.parametrize("force", [True, False])
    @patch('srv.modules.runners.osd.OSDUtil._lvm_zap', autospec=True)
    @patch('srv.modules.runners.osd.OSDUtil._delete_grain', autospec=True)
    @patch('srv.modules.runners.osd.OSDUtil._mark_destroyed', autospec=True)
    @patch('srv.modules.runners.osd.OSDUtil._is_empty', autospec=True)
    @patch('srv.modules.runners.osd.OSDUtil._service', autospec=True)
    @patch('srv.modules.runners.osd.OSDUtil._mark_osd', autospec=True)
    def test_replace(self, mark_osd_mock, service_mock, is_empty_mock,
                     mark_destoryed_mock, delete_grain_mock, lvm_zap_mock,
                     force, test_fix):
        """
        Doesn't is_empty if force=True
        """
        operation = 'replace'
        force = force
        test_fix = test_fix(operation=operation, force=force)
        test_fix.replace()
        test_fix._mark_osd.assert_called_once_with(test_fix, 'out')
        test_fix._service.assert_called_with(test_fix, 'stop')
        test_fix._service.assert_any_call(test_fix, 'disable')
        if not force:
            test_fix._is_empty.assert_called_once_with(test_fix)
            test_fix._mark_destroyed.assert_called_once_with(test_fix)
            test_fix._delete_grain.assert_called_once_with(test_fix)

    @pytest.mark.parametrize("force", [True, False])
    @patch('srv.modules.runners.osd.OSDUtil._lvm_zap', autospec=True)
    @patch('srv.modules.runners.osd.OSDUtil._delete_grain', autospec=True)
    @patch('srv.modules.runners.osd.OSDUtil._purge_osd', autospec=True)
    @patch('srv.modules.runners.osd.OSDUtil._empty_osd', autospec=True)
    @patch('srv.modules.runners.osd.OSDUtil._service', autospec=True)
    @patch('srv.modules.runners.osd.OSDUtil._mark_osd', autospec=True)
    def test_remove(self, mark_osd_mock, service_mock, is_empty_mock,
                    purge_osd_mock, delete_grain_mock, lvm_zap_mock, force,
                    test_fix):
        """
        Doesn't empty if force=True
        """
        operation = 'remove'
        force = force
        test_fix = test_fix(operation=operation, force=force)
        test_fix.remove()
        test_fix._mark_osd.assert_called_once_with(test_fix, 'out')
        test_fix._service.assert_called_with(test_fix, 'stop')
        test_fix._service.assert_any_call(test_fix, 'disable')
        if not force:
            test_fix._empty_osd.assert_called_once_with(test_fix)
        test_fix._purge_osd.assert_called_once_with(test_fix)
        test_fix._delete_grain.assert_called_once_with(test_fix)

    def test_delete_grain(self, test_fix):
        test_fix = test_fix()
        test_fix._delete_grain()
        test_fix.local.cmd.assert_called_once_with(
            "dummy_host",
            "osd.delete_grain", [test_fix.osd_id],
            tgt_type='glob')

    @patch(
        'srv.modules.runners.osd._master_minion',
        autospec=True,
        return_value="master_minion")
    @patch(
        'srv.modules.runners.osd.OSDUtil._wait_loop',
        autospec=True,
        return_value=True)
    def test_is_empty(self, wait_loop, master_minion, test_fix):
        test_fix = test_fix()
        test_fix._is_empty()
        test_fix.local.cmd.assert_called_once_with(
            "master_minion",
            "osd.wait_until_empty", [test_fix.osd_id],
            tgt_type='glob')
        assert wait_loop.called is True

    @patch(
        'srv.modules.runners.osd._master_minion',
        autospec=True,
        return_value="master_minion")
    @patch(
        'srv.modules.runners.osd.OSDUtil._wait_loop',
        autospec=True,
        return_value=True)
    def test_empty_osd(self, wait_loop, master_minion, test_fix):
        test_fix = test_fix()
        test_fix._empty_osd()
        test_fix.local.cmd.assert_called_once_with(
            "master_minion", "osd.empty", [test_fix.osd_id], tgt_type='glob')
        assert wait_loop.called is True

    @patch(
        'srv.modules.runners.osd.time.sleep', autospec=True, return_value=True)
    def test_wait_loop_1(self, time_mock, test_fix):
        """
        Message starts with Timeout expired
        expect func() to be called.
        func returns unexpected return output bogus
        """
        test_fix = test_fix()
        test_func = Mock(return_value="Unexpected return")
        ret = test_fix._wait_loop(test_func, 'Timeout expired')
        test_func.assert_called_once()
        assert ret is None  # it breaks (as in continue/break)

    @patch(
        'srv.modules.runners.osd.time.sleep', autospec=True, return_value=True)
    def test_wait_loop_2(self, time_mock, test_fix):
        """
        Message starts with Timeout expired
        expect func() to be called.
        func returns with osd.1 is safe to destroy
        """
        test_fix = test_fix()
        test_func = Mock(return_value="osd.1 is safe to destroy")
        ret = test_fix._wait_loop(test_func, 'Timeout expired')
        test_func.assert_called_once()
        assert ret is True

    @patch(
        'srv.modules.runners.osd.time.sleep', autospec=True, return_value=True)
    def test_wait_loop_3(self, time_mock, test_fix):
        """
        Message starts with Timeout expired
        expect func() to be called.
        func returns with Timeout again
        expect to call func() recursively until counter is hit.
        """
        test_fix = test_fix()
        test_func = Mock(return_value="Timeout expired")
        ret = test_fix._wait_loop(test_func, 'Timeout expired')
        test_func.call_count == 51
        assert ret is None

    @patch(
        'srv.modules.runners.osd.time.sleep', autospec=True, return_value=True)
    def test_wait_loop_4(self, time_mock, test_fix):
        """
        Message starts with Timeout expired
        expect func() to be called.
        func returns True
        expect to break immediately
        """
        test_fix = test_fix()
        test_func = Mock(return_value=True)
        ret = test_fix._wait_loop(test_func, 'Timeout expired')
        test_func.call_count == 0
        assert ret is None

    @patch('srv.modules.runners.osd.OSDUtil._mark_osd', autospec=True)
    @patch(
        'srv.modules.runners.osd._master_minion',
        autospec=True,
        return_value="master_minion")
    def test_recover_osd_state_in(self, master_minion, mark_osd_mock,
                                  test_fix):
        test_fix = test_fix()
        test_fix.recover_osd_state()
        test_fix._mark_osd.assert_called_once_with(test_fix, 'in')

    @patch('srv.modules.runners.osd.OSDUtil._mark_osd', autospec=True)
    @patch(
        'srv.modules.runners.osd._master_minion',
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

    @patch(
        'srv.modules.runners.osd._master_minion',
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
        'srv.modules.runners.osd._master_minion',
        autospec=True,
        return_value="master_minion")
    def test_mark_destroyed_fail(self, master_minion, test_fix):
        test_fix = test_fix()
        test_fix.local.cmd.return_value = {'node': 'Nope, some error'}
        with pytest.raises(RuntimeError):
            test_fix._mark_destroyed()

    @patch(
        'srv.modules.runners.osd._master_minion',
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
        'srv.modules.runners.osd._master_minion',
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
        'srv.modules.runners.osd._master_minion',
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
        'srv.modules.runners.osd._master_minion',
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
        'srv.modules.runners.osd._master_minion',
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
        'srv.modules.runners.osd._master_minion',
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

    def test_host_osds(self, test_fix):
        test_fix = test_fix()
        test_fix._host_osds()
        test_fix.local.cmd.assert_called_once_with(
            "I@roles:storage", 'osd.list', tgt_type='compound')

    @patch(
        'srv.modules.runners.osd._master_minion',
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
        'srv.modules.runners.osd._master_minion',
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
