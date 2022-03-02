from mock import patch, MagicMock, mock
from srv.modules.runners import rebuild
import pytest

class TestRebuild():
    """
    """
    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self.caplog = caplog

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_minions(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        local = localclient.return_value
        local.cmd.return_value = {'data1.ceph': 'data1.ceph'}
        rr = rebuild.Rebuild(['data1.ceph'])
        assert rr.minions == ['data1.ceph']

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_minions_targets(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        local = localclient.return_value
        local.cmd.return_value = {'data1.ceph': 'data1.ceph',
                                  'data2.ceph':'data2.ceph'}
        rr = rebuild.Rebuild(['I@roles:storage'])
        assert rr.minions == ['data1.ceph', 'data2.ceph']

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_minions_multiple(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        local = localclient.return_value
        local.cmd.return_value = {'data1.ceph': 'data1.ceph',
                                  'data2.ceph':'data2.ceph'}
        rr = rebuild.Rebuild(['data*.ceph', 'data*.ceph'])
        assert rr.minions == ['data1.ceph', 'data2.ceph']

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_osd_list(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        local = localclient.return_value
        local.cmd.return_value = {'data1.ceph': [0, 1, 2]}
        rr = rebuild.Rebuild(['data*.ceph'])
        result = rr._osd_list('data1.ceph')
        assert result == [0, 1, 2]

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_osd_list_no_match(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        local = localclient.return_value
        local.cmd.return_value = {'data1.ceph': [0, 1, 2]}
        rr = rebuild.Rebuild(['data*.ceph'])
        result = rr._osd_list('data2.ceph')
        assert result == None

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_validate_osd_df(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        local = localclient.return_value
        local.cmd.return_value = {}
        mm.return_value = 'admin'
        rr = rebuild.Rebuild(['data*.ceph'])

        osd_df = {'admin': {'nodes': '', 'summary':{'total_kb_avail': '0'}}}
        result = rr._validate_osd_df(osd_df)
        assert result == True

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_validate_osd_df_missing_mm(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        local = localclient.return_value
        local.cmd.return_value = {}
        mm.return_value = 'admin'
        rr = rebuild.Rebuild(['data*.ceph'])

        osd_df = {'': {'nodes': '', 'summary':{'total_kb_avail': '0'}}}
        result = rr._validate_osd_df(osd_df)
        assert result == False

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_validate_osd_df_missing_nodes(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        local = localclient.return_value
        local.cmd.return_value = {}
        mm.return_value = 'admin'
        rr = rebuild.Rebuild(['data*.ceph'])

        osd_df = {'admin': {'': '', 'summary':{'total_kb_avail': '0'}}}
        result = rr._validate_osd_df(osd_df)
        assert result == False

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_validate_osd_df_missing_summary(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        local = localclient.return_value
        local.cmd.return_value = {}
        mm.return_value = 'admin'
        rr = rebuild.Rebuild(['data*.ceph'])

        osd_df = {'admin': {'nodes': '', '':{'total_kb_avail': '0'}}}
        result = rr._validate_osd_df(osd_df)
        assert result == False

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_validate_osd_df_missing_total(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        local = localclient.return_value
        local.cmd.return_value = {}
        mm.return_value = 'admin'
        rr = rebuild.Rebuild(['data*.ceph'])

        osd_df = {'admin': {'nodes': '', 'summary':{'': '0'}}}
        result = rr._validate_osd_df(osd_df)
        assert result == False

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_safe(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        local = localclient.return_value
        local.cmd.return_value = {'admin': {'nodes': [
                                             {'id': 0, 'kb_used': 10},
                                             {'id': 1, 'kb_used': 10}
                                             ],
                                            'summary':{'total_kb_avail': 30}}}
        mm.return_value = 'admin'
        rr = rebuild.Rebuild(['data*.ceph'])

        result = rr.safe(['0', '1'])
        assert result == True

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_safe_fails(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        local = localclient.return_value
        local.cmd.return_value = {'admin': {'nodes': [
                                             {'id': 0, 'kb_used': 10},
                                             {'id': 1, 'kb_used': 10}
                                             ],
                                            'summary':{'total_kb_avail': 10}}}
        mm.return_value = 'admin'
        rr = rebuild.Rebuild(['data*.ceph'])

        result = rr.safe(['0', '1'])
        assert result == False

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_safe_fails_validation(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        local = localclient.return_value
        local.cmd.return_value = {'': {'nodes': [
                                             {'id': 0, 'kb_used': 10},
                                             {'id': 1, 'kb_used': 10}
                                             ],
                                            'summary':{'total_kb_avail': 10}}}
        mm.return_value = 'admin'
        rr = rebuild.Rebuild(['data*.ceph'])

        result = rr.safe(['0', '1'])
        assert result == False

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_check_failed(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        rr = rebuild.Rebuild(['data*.ceph'])

        ret = {0: True, 1:True}
        result = rr._check_failed(ret, 'data1.ceph')
        assert result == False
        assert rr.skipped == []

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_check_failed_finds_failure(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        rr = rebuild.Rebuild(['data*.ceph'])

        ret = {0: False, 1:True}
        result = rr._check_failed(ret, 'data1.ceph')
        assert result == True
        assert rr.skipped == ['data1.ceph']

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_check_failed_finds_error(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        rr = rebuild.Rebuild(['data*.ceph'])

        ret = "An error message"
        result = rr._check_failed(ret, 'data1.ceph')
        assert result == True
        assert rr.skipped == ['data1.ceph']

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_run(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        rr = rebuild.Rebuild(['data*.ceph'])
        rr._disengaged = mock.Mock()
        rr._disengaged.return_value = True
        rr.minions = ['data1.ceph']
        rr._osd_list = mock.Mock()
        rr._osd_list.return_value = [0, 1]
        rr.safe = mock.Mock()
        rr.safe.return_value = True
        rr._busy_wait = mock.Mock()
        rr.runner.cmd = mock.Mock()
        rr.runner.cmd.return_value = {}
        rr._check_failed = mock.Mock()
        rr._check_failed.return_value = False
        rr._skipped_summary = mock.Mock()

        result = rr.run()
        assert result == ""
        assert rr._osd_list.called
        assert rr.safe.called
        assert rr.runner.cmd.called
        assert rr._check_failed.called
        assert rr._skipped_summary.called

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_run_multiple(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        rr = rebuild.Rebuild(['data*.ceph'])
        rr._disengaged = mock.Mock()
        rr._disengaged.return_value = True
        rr.minions = ['data1.ceph', 'data2.ceph']
        rr._osd_list = mock.Mock()
        rr._osd_list.return_value = [0, 1]
        rr.safe = mock.Mock()
        rr.safe.return_value = True
        rr._busy_wait = mock.Mock()
        rr.runner.cmd = mock.Mock()
        rr.runner.cmd.return_value = {}
        rr._check_failed = mock.Mock()
        rr._check_failed.return_value = False
        rr._skipped_summary = mock.Mock()

        result = rr.run()
        assert result == ""
        assert rr._osd_list.call_count == 2
        assert rr.safe.call_count == 2
        assert rr.runner.cmd.call_count == 4
        assert rr._check_failed.call_count == 2
        assert rr._skipped_summary.called

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_run_check_only(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        rr = rebuild.Rebuild(['data*.ceph'])
        rr._disengaged = mock.Mock()
        rr._disengaged.return_value = True
        rr.minions = ['data1.ceph']
        rr._osd_list = mock.Mock()
        rr._osd_list.return_value = [0, 1]
        rr.safe = mock.Mock()
        rr.safe.return_value = True
        rr.runner.cmd = mock.Mock()
        rr.runner.cmd.return_value = {}
        rr._check_failed = mock.Mock()
        rr._check_failed.return_value = False
        rr._skipped_summary = mock.Mock()

        result = rr.run(checkonly=True)
        assert result == ""
        assert rr._osd_list.called
        assert rr.safe.called
        assert rr.runner.cmd.called is False
        assert rr._check_failed.called is False
        assert rr._skipped_summary.called

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_run_safety_engaged(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        rr = rebuild.Rebuild(['data*.ceph'])
        rr._disengaged = mock.Mock()
        rr._disengaged.return_value = False
        rr.minions = ['data1.ceph']
        rr._osd_list = mock.Mock()
        rr._osd_list.return_value = [0, 1]
        rr.safe = mock.Mock()
        rr.safe.return_value = True
        rr.runner.cmd = mock.Mock()
        rr.runner.cmd.return_value = {}
        rr._check_failed = mock.Mock()
        rr._check_failed.return_value = False
        rr._skipped_summary = mock.Mock()

        result = rr.run()
        assert result == ""
        assert rr._osd_list.called is False
        assert rr.safe.called is False
        assert rr.runner.cmd.called is False
        assert rr._check_failed.called is False
        assert rr._skipped_summary.called is False

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_run_no_remove(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        rr = rebuild.Rebuild(['data*.ceph'])
        rr._disengaged = mock.Mock()
        rr._disengaged.return_value = True
        rr.minions = ['data1.ceph']
        rr._osd_list = mock.Mock()
        rr._osd_list.return_value = []
        rr.safe = mock.Mock()
        rr.safe.return_value = True
        rr.runner.cmd = mock.Mock()
        rr.runner.cmd.return_value = {}
        rr._check_failed = mock.Mock()
        rr._check_failed.return_value = False
        rr._skipped_summary = mock.Mock()

        result = rr.run()
        assert result == ""
        assert rr._osd_list.called
        assert rr.safe.called is False
        assert rr.runner.cmd.called
        assert rr._check_failed.called is False
        assert rr._skipped_summary.called

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_run_not_safe(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        rr = rebuild.Rebuild(['data*.ceph'])
        rr._disengaged = mock.Mock()
        rr._disengaged.return_value = True
        rr.minions = ['data1.ceph']
        rr._osd_list = mock.Mock()
        rr._osd_list.return_value = [0, 1]
        rr.safe = mock.Mock()
        rr.safe.return_value = False
        rr.runner.cmd = mock.Mock()
        rr.runner.cmd.return_value = {}
        rr._check_failed = mock.Mock()
        rr._check_failed.return_value = False
        rr._skipped_summary = mock.Mock()

        result = rr.run()
        assert result == ""
        assert rr._osd_list.called
        assert rr.safe.called
        assert rr.runner.cmd.called is False
        assert rr._check_failed.called is False
        assert rr._skipped_summary.called is False

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_run_remove_failed(self, localclient, runner, mm):
        rebuild.__opts__ = {}

        rr = rebuild.Rebuild(['data*.ceph'])
        rr._disengaged = mock.Mock()
        rr._disengaged.return_value = True
        rr.minions = ['data1.ceph']
        rr._osd_list = mock.Mock()
        rr._osd_list.return_value = [0, 1]
        rr.safe = mock.Mock()
        rr.safe.return_value = True
        rr._busy_wait = mock.Mock()
        rr.runner.cmd = mock.Mock()
        rr.runner.cmd.return_value = {}
        rr._check_failed = mock.Mock()
        rr._check_failed.return_value = True
        rr._skipped_summary = mock.Mock()

        result = rr.run()
        assert result == ""
        assert rr._osd_list.called
        assert rr.safe.called
        assert rr.runner.cmd.called
        assert rr._check_failed.called
        assert rr._skipped_summary.called

    @patch('srv.modules.runners.rebuild.master_minion', autospec=True)
    @patch('salt.runner.Runner', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    def test_run_check_warning_message_when_fails(self, localclient, runner, mm):
        rebuild.__opts__ = {}
        mm.return_value = 'master_minion'
        rr = rebuild.Rebuild(['data*.ceph'])
        rr.local.cmd = mock.Mock()
        class LocalCmdReturnValues(object):
            def __init__(self, *fns):
                self.fs = iter(fns)
            def __call__(self, *args, **kwargs):
                f = next(self.fs)
                return f(*args, **kwargs)
        def scrubbing(*args, **kwargs):
            return {"master_minion": {
                        "result": False,
                        "message": ("Timeout expired waiting on active+clean: "
                                    "PGs are scrubbing, "
                                    "disable scrubbing and retry."),
                        "num": 128}}
        def ok(*args, **kwargs):
            return {"master_minion": {
                        "result": True, "message": "PGs are active+clean", "num": 128}}

        rr.local.cmd.side_effect = LocalCmdReturnValues(scrubbing, ok)
        rr._busy_wait()
        # we're expecting to see 1 warning line with the pgs scrubbing message
        messages_expected = [rec for rec in self.caplog.records if 'PGs are scrubbing' in rec.message]
        assert len(messages_expected) == 1
        assert messages_expected[0].message == "Timeout expired waiting on active+clean: PGs are scrubbing, disable scrubbing and retry."
