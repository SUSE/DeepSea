import pytest
import sys
sys.path.insert(0, 'srv/salt/_modules')
from srv.salt._modules import cephprocesses, helper
from mock import MagicMock, patch, mock_open, mock, create_autospec, ANY
from tests.unit.helper.output import OutputHelper
from tests.unit.helper.fixtures import helper_specs
from collections import namedtuple

DEFAULT_MODULE=cephprocesses

class MockedPsUtil(object):

    def __init__(self, name, pid, uid, exe, osd_id=0):
        self._name = name
        self._uid = uid
        self._exe = exe
        self.pid = pid
        self.osd_id = osd_id

    def name(self):
        return self._name

    def exe(self):
        return self._exe

    def uids(self):
        Puids = namedtuple('Puids', 'real effective saved')
        return Puids(self._uid, 0, 0)

    def cmdline(self):
        return ['/usr/bin/ceph-osd', '-f', '--cluster', 'ceph', '--id', '{}'.format(self.osd_id), '--setuser', 'ceph', '--setgroup', 'ceph']

    def status(self):
        return 'running'


class TestCephprocessesProcInfo():

    @pytest.fixture(scope='class')
    def cpr(self):
        yield MockedPsUtil('ceph-osd', 0, 0, '/usr/bin/ceph-osd')

    def test_map_open_proc_to_osd_id_1(self, cpr):
        """
        passing a osd_id of 1 to the process, it also mocks the 'open_files'
        namedtuple to match that ID. This tests the regex.
        """
        proc = MockedPsUtil('ceph-osd', 0, 0, '/usr/bin/ceph-osd', osd_id=1)
        procinfo = cephprocesses.ProcInfo(proc)
        assert procinfo.osd_id == '1'

    def test_map_open_proc_to_osd_id_2digits(self):
        """
        passing a osd_id of 20 to the process, it also mocks the 'open_files'
        namedtuple to match that ID. This tests the regex.
        """
        proc = MockedPsUtil('ceph-osd', 0, 0, '/usr/bin/ceph-osd', osd_id=20)
        procinfo = cephprocesses.ProcInfo(proc)
        assert procinfo.osd_id == '20'

    def test_map_open_proc_to_osd_id_multiple_digits(self):
        """
        passing a osd_id of 99999 to the process, it also mocks the 'open_files'
        namedtuple to match that ID. This tests the regex.
        """
        proc = MockedPsUtil('ceph-osd', 0, 0, '/usr/bin/ceph-osd', osd_id=99999)
        procinfo = cephprocesses.ProcInfo(proc)
        assert procinfo.osd_id == '99999'

    def test_map_open_proc_to_osd_id_multiple_raises(self):
        """
        passing a osd_id of None  to the process, it also mocks the 'open_files'
        namedtuple to match that ID. This tests the Exception
        """
        proc = MockedPsUtil('ceph-osd', 0, 0, '/usr/bin/ceph-osd', osd_id='')
        with pytest.raises(cephprocesses.NoOSDIDFound):
            procinfo = cephprocesses.ProcInfo(proc)

class TestMetaCheck():

    @pytest.fixture(scope='class')
    def mc(self):
        cephprocesses.__grains__ = {'host': 'a_hostname'}
        self.set_osd_list([])
        yield cephprocesses.MetaCheck()

    def set_osd_list(self, osd_list):
        cephprocesses.__salt__ = {'osd.list': lambda : osd_list}

    @pytest.mark.skip(reason='Not fully implemented yet')
    def test_blacklist(self):
        pass

    @pytest.mark.skip(reason='Not fully implemented yet')
    def test_expected_osds(self, mc):
        """
        If no blacklist is set, expected OSDs are the osds that
        are returned from __salt__['osd.list']
        """
        expect = ['1', '2']
        self.set_osd_list(expect)
        assert mc.expected_osds == expect

    @pytest.mark.skip(reason='Not fully implemented yet')
    def test_expected_osds_blacklist(self, mc):
        """
        if OSDs are blacklisted, expect to see it removed
        from the list
        """
        expect = ['1', '2', '3']
        mc.blacklist = {'ceph-osd': ['2']}
        self.set_osd_list(expect)
        assert mc.expected_osds == ['1', '3']

    def mock_up(self):
        ups = []
        for prc_name, bin_names in cephprocesses.processes.items():
            for bin_name in bin_names:
                proc = MockedPsUtil(bin_name, 0, 0, '/usr/bin/{}'.format(bin_name))
                procinfo = cephprocesses.ProcInfo(proc)
                ups.append(procinfo)
        return ups

    def test_filter_ceph_osd(self, mc):
        """
        Len = 1 because we source from processes list
        """
        mc.up = self.mock_up()
        expected_len = 1
        ret = mc.filter_for('ceph-osd')
        assert len(ret) == expected_len
        assert ret[0].name == 'ceph-osd'

    def test_filter_ceph_mon(self, mc):
        mc.up = self.mock_up()
        expected_len = 1
        ret = mc.filter_for('ceph-mon')
        assert len(ret) == expected_len
        assert ret[0].name == 'ceph-mon'

    def test_filter_ceph_osd_multiple(self, mc):
        expected_len = 10
        for i in range(1, expected_len):
            mc.up.extend(self.mock_up())
        ret = mc.filter_for('ceph-osd')
        assert len(ret) == expected_len
        assert ret[0].name == 'ceph-osd'

    def build_proc(self, role_name, proc_name, uid=0):
        proc = MockedPsUtil(proc_name, 0, uid, '/usr/bin/{}'.format(proc_name))
        return cephprocesses.ProcInfo(proc)

    def test_add_storage(self, mc):
        mc.up = []
        role_name = 'storage'
        proc_name = 'ceph-osd'
        mc.add(self.build_proc(role_name, proc_name), role_name)
        assert len(mc.up) == 1
        assert mc.up[0].name == 'ceph-osd'

    def test_add_mon(self, mc):
        mc.up = []
        role_name = 'mon'
        proc_name = 'ceph-mon'

        mc.add(self.build_proc(role_name, proc_name), role_name)
        assert len(mc.up) == 1
        assert mc.up[0].name == proc_name

    def test_add_mgr(self, mc):
        mc.up = []
        role_name = 'mgr'
        proc_name = 'ceph-mgr'
        mc.add(self.build_proc(role_name, proc_name), role_name)
        assert len(mc.up) == 1
        assert mc.up[0].name == proc_name

    def test_add_mds(self, mc):
        mc.up = []
        role_name = 'mds'
        proc_name = 'ceph-mds'
        mc.add(self.build_proc(role_name, proc_name), role_name)
        assert len(mc.up) == 1
        assert mc.up[0].name == proc_name

    def test_add_igw(self, mc):
        mc.up = []
        role_name = 'mds'
        proc_name = 'ceph-mds'
        mc.add(self.build_proc(role_name, proc_name), role_name)
        assert len(mc.up) == 1
        assert mc.up[0].name == proc_name

    def test_add_rgw(self, mc):
        mc.up = []
        role_name = 'rgw'
        proc_name = 'radosgw'
        mc.add(self.build_proc(role_name, proc_name), role_name)
        assert len(mc.up) == 1
        assert mc.up[0].name == proc_name

    def test_add_igw(self, mc):
        mc.up = []
        role_name = 'igw'
        proc_name = 'lrbd'
        mc.add(self.build_proc(role_name, proc_name), role_name)
        assert len(mc.up) == 1
        assert mc.up[0].name == proc_name

    def test_add_ganesha(self, mc):
        mc.up = []
        role_name = 'ganesha'
        proc_name = 'ganesha.nfsd'
        proc_name2 = 'rpcbind'
        proc_name3 = 'rpc.statd'
        mc.add(self.build_proc(role_name, proc_name), role_name)
        mc.add(self.build_proc(role_name, proc_name2), role_name)
        mc.add(self.build_proc(role_name, proc_name3), role_name)
        assert len(mc.up) == 3
        assert mc.up[0].name == proc_name
        assert mc.up[1].name == proc_name2
        assert mc.up[2].name == proc_name3

    @pytest.mark.skip(reason="openattic will be replaced by ceph-dashboard")
    def test_add_openattic(self, mc):
        mc.up = []
        role_name = 'openattic'
        proc_name = 'httpd-prefork'
        proc = self.build_proc(role_name, proc_name)
        proc.uid_name = 'openattic'
        mc.add(proc, role_name)
        assert len(mc.up) == 1
        assert mc.up[0].name == proc_name

    @pytest.mark.skip(reason="openattic will be replaced by ceph-dashboard")
    def test_add_openattic_negative(self, mc):
        mc.up = []
        role_name = 'openattic'
        proc_name = 'httpd-prefork'
        proc = self.build_proc(role_name, proc_name)
        # not fulfilled the if branch
        proc.uid_name = 'openatticNOTNOT'
        mc.add(proc, role_name)
        assert len(mc.up) == 0

    def test_check_inverts_positive(self, mc):
        mc.up = []
        role_name = 'igw'
        proc_name = 'lrbd'
        proc = self.build_proc(role_name, proc_name)
        assert mc.running == True
        mc.up.append(proc)
        mc.check_inverts(role_name)
        # TODO: Expect a log.error
        assert mc.running == False

    def test_check_inverts_negative(self, mc):
        mc.up = []
        mc.running = True
        role_name = 'mds'
        proc_name = 'ceph-mds'
        proc = self.build_proc(role_name, proc_name)
        assert mc.running == True
        mc.up.append(proc)
        mc.check_inverts(role_name)
        assert mc.running == True

    def test_check_absents(self, mc):
        role_name = 'mds'
        proc_name = 'ceph-mds'
        proc = self.build_proc(role_name, proc_name)
        mc.up = [proc]
        mc.check_absents(role_name)
        assert len(mc.down) == 0

    def test_check_absents_negative(self, mc):
        mc.up = []
        role_name = 'mds'
        mc.check_absents(role_name)
        assert len(mc.down) == 1

    def test_check_absents_negative_ganesha(self, mc):
        mc.down = []
        role_name = 'ganesha'
        proc_name1 = 'ganesha.nfsd'
        proc_name2 = 'rpcbind'
        # expect to miss rpc.statd
        proc1 = self.build_proc(role_name, proc_name1)
        proc2 = self.build_proc(role_name, proc_name2)
        mc.up = [proc1, proc2]
        mc.check_absents(role_name)
        assert len(mc.down) == 1
        assert mc.down[0] == 'rpc.statd'

    @mock.patch('srv.salt._modules.cephprocesses.MetaCheck.filter_for')
    def test_missing_osds(self, filter_mock, mc):
        """
        osd.list return 1,2,3
        blacklist holds 2
        expected_osds will be 1,3
        Now only 1 can be found in filter_for(ceph-osd)
        Expect to return 3
        """
        self.set_osd_list(['1', '2', '3'])
        mc.blacklist = {'ceph-osd': ['2']}
        proc = MockedPsUtil('ceph-osd', 0, 0, '/usr/bin/ceph-osd', osd_id=1)
        filter_mock.return_value = [proc]
        assert mc._missing_osds == ['3']

    @mock.patch('srv.salt._modules.cephprocesses.MetaCheck.filter_for')
    def test_missing_osds_no_return(self, filter_mock, mc):
        """
        osd.list return 1,2,3
        blacklist holds 2
        expected_osds will be 1,3
        1,3 can be found in filter_for(ceph-osd)
        Expect to return 3
        """
        proc = MockedPsUtil('ceph-osd', 0, 0, '/usr/bin/ceph-osd', osd_id=1)
        proc1 = MockedPsUtil('ceph-osd', 0, 0, '/usr/bin/ceph-osd', osd_id=3)
        filter_mock.return_value = [proc, proc1]
        assert mc._missing_osds == []

    @mock.patch('srv.salt._modules.cephprocesses.MetaCheck.filter_for')
    def test_insufficient_osd_count(self, filter_mock, mc):
        """
        expected_osds will be 1,3 -> len == 2
        """
        proc = MockedPsUtil('ceph-osd', 0, 0, '/usr/bin/ceph-osd', osd_id=1)
        filter_mock.return_value = [proc]
        # TODO: check for logging
        assert mc.insufficient_osd_count == False
        mc._insufficient_osd_count()
        assert mc.insufficient_osd_count == True

    @mock.patch('srv.salt._modules.cephprocesses.MetaCheck.filter_for')
    def test_insufficient_osd_count_positive(self, filter_mock, mc):
        """
        expected_osds will be 1,3 -> len == 2
        """
        mc.insufficient_osd_count = False
        proc = MockedPsUtil('ceph-osd', 0, 0, '/usr/bin/ceph-osd', osd_id=1)
        proc1 = MockedPsUtil('ceph-osd', 0, 0, '/usr/bin/ceph-osd', osd_id=1)
        filter_mock.return_value = [proc, proc1]
        # TODO: check for logging
        assert mc.insufficient_osd_count == False
        mc._insufficient_osd_count()
        assert mc.insufficient_osd_count == False

    @mock.patch('srv.salt._modules.cephprocesses.MetaCheck.filter_for')
    @mock.patch('srv.salt._modules.cephprocesses.MetaCheck._insufficient_osd_count')
    def test_check_osd(self, insuf_mock, filter_mock, mc):
        """
        Filter for returns something
        insuff is True
        """
        mc.running = True
        filter_mock.return_value = ['notnull']
        mc.insufficient_osd_count = True
        mc.check_osds()
        assert mc.running == False

    @mock.patch('srv.salt._modules.cephprocesses.MetaCheck.filter_for')
    @mock.patch('srv.salt._modules.cephprocesses.MetaCheck._insufficient_osd_count')
    def test_check_osd_1(self, insuf_mock, filter_mock, mc):
        """
        filter_for does not return
        """
        mc.running = True
        filter_mock.return_value = []
        mc.check_osds()
        assert mc.running == True

    @mock.patch('srv.salt._modules.cephprocesses.MetaCheck.filter_for')
    @mock.patch('srv.salt._modules.cephprocesses.MetaCheck._insufficient_osd_count')
    def test_check_osd_2(self, insuf_mock, filter_mock, mc):
        """
        filter_for does return something
        but isuff is False
        """
        mc.running = True
        filter_mock.return_value = ['notnull']
        mc.insufficient_osd_count = False
        mc.check_osds()
        assert mc.running == True

    def test_report_empty(self, mc):
        mc.up = []
        mc.down = []
        assert mc.report() == {'up': {}, 'down': {}}

    def test_report_up(self, mc):
        role_name = 'mds'
        proc_name = 'ceph-mds'
        proc = self.build_proc(role_name, proc_name)
        mc.up = [proc]
        mc.down = []
        assert mc.report() == {'up': {'ceph-mds': [0]}, 'down': {}}

    def test_report_down_not_disabled(self, mc):
        with mock.patch('srv.salt._modules.cephprocesses.SystemdUnit.is_disabled', new_callable=mock.PropertyMock) as mock_my_property:
            mock_my_property.return_value = False
            proc_name = 'ceph-mds'
            mc.up = []
            mc.down = [proc_name]
            assert mc.report() == {'up': {}, 'down': {'ceph-mds': 'ceph-mds'}}

    def test_report_down_disabled(self, mc):
        with mock.patch('srv.salt._modules.cephprocesses.SystemdUnit.is_disabled', new_callable=mock.PropertyMock) as mock_my_property:
            mock_my_property.return_value = True
            proc_name = 'ceph-mds'
            mc.up = []
            mc.down = [proc_name]
            assert mc.report() == {'up': {}, 'down': {}}

    def test_report_up_down(self, mc):
        role_name = 'storage'
        proc_name = 'ceph-osd'
        proc_name_down = 'ceph-mds'
        proc = self.build_proc(role_name, proc_name)
        mc.up = [proc]
        mc.down = [proc_name_down]
        assert mc.report() == {'up': {'ceph-osd': [0]}, 'down': {'ceph-mds': 'ceph-mds'}}

    @mock.patch('srv.salt._modules.cephprocesses.MetaCheck._missing_osds', new_callable=mock.PropertyMock)
    def test_report_up_down_down(self, missing_mock, mc):
        """
        expected 1,3 up
        0 is down
        """
        # 2 is blacklisted
        missing_mock.return_value = ['1', '3']
        role_name = 'storage'
        proc_name = 'ceph-osd'
        proc_name_down = 'ceph-mds'
        mc.insufficient_osd_count = True
        proc = self.build_proc(role_name, proc_name)
        mc.up = [proc]
        mc.down = [proc_name_down]
        assert mc.report() == {'up': {'ceph-osd': [0]}, 'down': {'ceph-mds': 'ceph-mds', 'ceph-osd': ['1', '3']}}


class TestInstanceMethods():

    def test_check(self):
        """
        Exit if there is no pillar data
        """
        cephprocesses.__pillar__ = {}
        assert cephprocesses.check() == False

    @mock.patch('srv.salt._modules.cephprocesses.psutil')
    @mock.patch('srv.salt._modules.cephprocesses.MetaCheck')
    @mock.patch('srv.salt._modules.cephprocesses.ProcInfo')
    def test_check_1(self, proc_mock, meta_mock, psutil_mock):
        """
        Exit if there is pillar data but no roles in it
        """
        cephprocesses.__pillar__ = {'NOroles': ['dummy']}
        assert cephprocesses.check() == False

    @pytest.mark.parametrize("test_input,expected", [
        ("mgr", 'mgr'),
        ("mon", 'mon'),
        ("mds", 'mds'),
        ("openattic", 'openattic'),
        ("rgw", 'rgw'),
        ("benchmark-rbd", 'benchmark-rbd'),
        ("storage", 'storage'),
        ("ganesha", 'ganesha')
    ])
    @mock.patch('srv.salt._modules.cephprocesses.psutil.process_iter')
    @mock.patch('srv.salt._modules.cephprocesses.MetaCheck.report')
    @mock.patch('srv.salt._modules.cephprocesses.MetaCheck.check_absents')
    @mock.patch('srv.salt._modules.cephprocesses.MetaCheck.check_inverts')
    @mock.patch('srv.salt._modules.cephprocesses.MetaCheck.check_osds')
    @mock.patch('srv.salt._modules.cephprocesses.MetaCheck.add')
    @mock.patch('srv.salt._modules.cephprocesses.ProcInfo')
    def test_check_2(self, proc_mock, meta_mock, mock_check_osds, meta_check_invert, meta_check_absent, mock_report, psutil_mock, test_input, expected):
        """
        Parameterized test to verify that roles get passed down to methods
        """
        role = [test_input]
        cephprocesses.__pillar__ = {'roles': role}
        psutil_mock.return_value = ['proc1']
        cephprocesses.check()
        proc_mock.assert_called_with('proc1')
        # ANY instance of ProcInfo
        meta_mock.assert_called_with(ANY, expected)
        meta_check_invert.assert_called_with(expected)
        meta_check_absent.assert_called_with(expected)
        mock_check_osds.assert_called_once is False
        mock_report.assert_called

class TestSystemdUnit():


    def test_service_names_default_return(self):
        obj = cephprocesses.SystemdUnit()
        assert obj.service_names == []

    def test_service_names_osd_no_id(self):
        obj = cephprocesses.SystemdUnit('ceph-osd')
        assert obj.service_names == []

    def test_service_names_osd(self):
        obj = cephprocesses.SystemdUnit('ceph-osd', 1)
        assert obj.service_names == ['ceph-osd@1']

    @pytest.mark.parametrize('proc_name', ['ceph-mon',
                                           'ceph-mgr',
                                           'ceph-mds'])
    def test_service_names_with_grains_default(self, proc_name):
        cephprocesses.__grains__ = {'host': 'a_host'}
        obj = cephprocesses.SystemdUnit(proc_name)
        assert obj.service_names == ['{}@{}'.format(proc_name, 'a_host')]

    @pytest.mark.parametrize('proc_name', ['radosgw'])
    def test_service_names_with_grains_non_default(self, proc_name):
        cephprocesses.__grains__ = {'host': 'a_host'}
        obj = cephprocesses.SystemdUnit(proc_name)
        assert obj.service_names == ['{}@{}'.format('ceph-radosgw', 'a_host')]

    @pytest.mark.parametrize('proc_name', ['ganesha.nfsd'])
    def test_service_names_ganesha(self, proc_name):
        obj = cephprocesses.SystemdUnit(proc_name)
        assert obj.service_names == ['nfs-ganesha', 'rpcbind']

    @pytest.mark.parametrize('proc_name', ['lrbd'])
    def test_service_names_lrbd(self, proc_name):
        obj = cephprocesses.SystemdUnit(proc_name)
        assert obj.service_names == ['lrbd']

    @patch('srv.salt._modules.cephprocesses.Popen')
    def test_is_disabled_no_service_names(self, popen_mock):
        ret = cephprocesses.SystemdUnit().is_disabled
        assert ret is False

    @patch('srv.salt._modules.cephprocesses.log')
    @patch('srv.salt._modules.cephprocesses.Popen')
    def test_is_disabled_1(self, po, log):
        """
        po returns 'enabled\n'
        log should be called. (once)

        """
        cephprocesses.__grains__ = {'host': 'a_host'}
        po.return_value.communicate.return_value = (b"enabled\n ", "")
        ret = cephprocesses.SystemdUnit('ceph-mon').is_disabled
        assert ret is False
        log.info.assert_called_once_with('Found ceph-mon@a_host to be enabled')

    @patch('srv.salt._modules.cephprocesses.log')
    @patch('srv.salt._modules.cephprocesses.Popen')
    def test_is_disabled_2(self, po, log):
        """
        po returns 'disabled\n'
        log should be called. (once)
        """
        cephprocesses.__grains__ = {'host': 'a_host'}
        po.return_value.communicate.return_value = (b"disabled\n ", "")
        ret = cephprocesses.SystemdUnit('ceph-mon').is_disabled
        assert ret is True
        log.info.assert_called_once_with('Found ceph-mon@a_host to be disabled')

    @patch('srv.salt._modules.cephprocesses.log')
    @patch('srv.salt._modules.cephprocesses.Popen')
    def test_is_disabled_3(self, po, log):
        """
        po returns 'undefinded\n'
        log should be called. (once)
        """
        cephprocesses.__grains__ = {'host': 'a_host'}
        po.return_value.communicate.return_value = (b"undefined\n ", "")
        ret = cephprocesses.SystemdUnit('ceph-mon').is_disabled
        assert ret is False
        log.info.assert_called_once_with('Expected to get disabled/enabled but got undefined instead')

    @patch('srv.salt._modules.cephprocesses.log')
    @patch('srv.salt._modules.cephprocesses.Popen')
    def test_is_disabled_4(self, po, log):
        """
        multiple entries in self.service_names
        one is enabled, one is disabled.
        expect to get True
        log should be called. (twice)
        """
        cephprocesses.__grains__ = {'host': 'a_host'}
        po.return_value.communicate.side_effect = [(b"enabled\n ", ""), (b"disabled\n ", "")]
        ret = cephprocesses.SystemdUnit('ganesha.nfsd').is_disabled
        assert ret is True
        log.info.assert_called_with('Found rpcbind to be disabled')

    @pytest.mark.skip(reason='Cant reproduce it in the tests, but can in the shell..')
    @patch('srv.salt._modules.cephprocesses.log')
    @patch('srv.salt._modules.cephprocesses.Popen')
    def test_is_disabled_5(self, po, log):
        """
        test for AttributeError
        """
        cephprocesses.__grains__ = {'host': 'a_host'}
        po.return_value.communicate.return_value = ("\n", "")
        with pytest.raises(AttributeError):
            ret = cephprocesses.SystemdUnit('ganesha.nfsd').is_disabled
            assert ret is False
            log.error.assert_called_with('Could not decode type->')

    @patch('srv.salt._modules.cephprocesses.log')
    @patch('srv.salt._modules.cephprocesses.Popen')
    def test_is_disabled_6(self, po, log):
        """
        stderr
        """
        cephprocesses.__grains__ = {'host': 'a_host'}
        po.return_value.communicate.return_value = ("", "stderr")
        ret = cephprocesses.SystemdUnit('ceph-mon').is_disabled
        assert ret is False
        log.error.assert_called_once_with('Requesting the is-enabled flag from ceph-mon@a_host has resulted in stderr')
