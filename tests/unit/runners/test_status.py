from mock import patch
import pytest
from srv.modules.runners import status
from tests.unit.helper.output import OutputHelper


class TestStatusReport():

    def versions(self):
        return {'salt': {
                  'common_version': '2016.11.4', 
                  'old_version': '2015.0.1'},
                'os': {
                  'common_version': 'SUSE Linux Enterprise Server 12 SP3', 
                  'old_version': 'SUSE Linux Enterprise Server 12 SP2'},
                'ceph': {
                  'common_version': 'ceph version 12.0.2-269-g9148e53 (9148e530e27266064877e632ccadecb4979b0904)',
                  'old_version': 'ceph version 10.0.2-269-g9148e53 (9148e530e27266064881e628ccadecb4975b0904)'}
                  }

    def alter_input(self, recurrence=1, reverse=False):
        """
        Altering the default return from salt to be able to test multiple
        scenarios without hardcoding
        """
        helper = OutputHelper()


        common_version = 'common_version'
        old_version = 'old_version'
        if reverse:
            common_version = 'old_version'
            old_version = 'common_version'

        expect = {'statusreport': [{'ceph': '', 'salt': '', 'os': ''}, {'out of sync': {}}]}

        salt_versions = helper.salt_versions
        os_codenames = helper.os_codenames
        ceph_versions = helper.ceph_versions

        tuple_data = [('salt', salt_versions), ('os', os_codenames), ('ceph', ceph_versions)]

        for key, data in tuple_data:
            cv = self.versions()[key][common_version]
            ov = self.versions()[key][old_version]
            expect['statusreport'][0][key] = cv

            # if reverse, set the data to the old_values
            if reverse:
                for node,value in data.iteritems():
                    data[node] = data[node].replace(ov, cv)
            
            for count, (node, value) in enumerate(data.iteritems(), 0):
                if count < recurrence:
                    data[node] = ov
                    if node not in expect['statusreport'][1]['out of sync']:
                        expect['statusreport'][1]['out of sync'].update({node: {}})
                    expect['statusreport'][1]['out of sync'][node].update({key: ov})
                        
        return salt_versions, os_codenames, ceph_versions, expect

    @patch('srv.modules.runners.status._get_data')
    def test_report_4_of_9(self, data):
        """
        4 are off, 5 are in sync
        Expecting to have the Common Version to be:
        salt: 2016.11.4
        os: SLE12SP3
        ceph_versions: ceph version 12.0.2
        Expecting to have 4 nodes in the out of sync list
        """

        salt_versions, os_codenames, ceph_versions, expect = self.alter_input(recurrence=4)

        
        data.return_value = os_codenames, salt_versions, ceph_versions
        ret = status.report(return_data=True)

        for ident in ['salt', 'ceph', 'os']:
            assert ret['statusreport'][0][ident] == self.versions()[ident]['common_version']
        assert ret == expect
        assert len(ret['statusreport'][1]['out of sync'].keys()) == 4

    @patch('srv.modules.runners.status._get_data')
    def test_report_3_of_9(self, data):
        """
        3 are off, 6 are in sync
        Expecting to have the Common Version to be:
        salt: 2016.11.4
        os: SLE12SP3
        ceph_versions: ceph version 12.0.2
        Expecting to have 3 nodes in the out of sync list
        """

        salt_versions, os_codenames, ceph_versions, expect = self.alter_input(recurrence=3)
        
        data.return_value = os_codenames, salt_versions, ceph_versions
        ret = status.report(return_data=True)

        for ident in ['salt', 'ceph', 'os']:
            assert ret['statusreport'][0][ident] == self.versions()[ident]['common_version']
        assert ret == expect
        assert len(ret['statusreport'][1]['out of sync'].keys()) == 3

    @patch('srv.modules.runners.status._get_data')
    def test_report_1_of_9(self, data):
        """
        1 are off, 8 are in sync
        Expecting to have the Common Version to be:
        salt: 2016.11.4
        os: SLE12SP3
        ceph_versions: ceph version 12.0.2
        Expecting to have 1 nodes in the out of sync list
        """

        salt_versions, os_codenames, ceph_versions, expect = self.alter_input(recurrence=1)
        
        data.return_value = os_codenames, salt_versions, ceph_versions
        ret = status.report(return_data=True)

        for ident in ['salt', 'ceph', 'os']:
            assert ret['statusreport'][0][ident] == self.versions()[ident]['common_version']
        assert ret == expect
        assert len(ret['statusreport'][1]['out of sync'].keys()) == 1

    @patch('srv.modules.runners.status._get_data')
    def test_report_0_of_9(self, data):
        """
        0 are off, all are in sync
        Expecting to have the Common Version to be:
        salt: 2016.11.4
        os: SLE12SP3
        ceph_versions: ceph version 12.0.2
        Expecting to have 0 nodes in the out of sync list
        """

        salt_versions, os_codenames, ceph_versions, expect = self.alter_input(recurrence=0)
        
        data.return_value = os_codenames, salt_versions, ceph_versions
        ret = status.report(return_data=True)

        for ident in ['salt', 'ceph', 'os']:
            assert ret['statusreport'][0][ident] == self.versions()[ident]['common_version']
        assert ret == expect
        assert len(ret['statusreport'][1]['out of sync'].keys()) == 0

    @patch('srv.modules.runners.status._get_data')
    def test_report_5_of_9(self, data):
        """

        5 are off, 4 are in sync
        which means that common values 
        will be the old_versions

        salt: 2015.0.1
        os: SLE12SP2
        ceph_versions: ceph version 10.0.2

        Expecting to have 4 nodes in the out of sync list
        """

        salt_versions, os_codenames, ceph_versions, expect = self.alter_input(recurrence=4, reverse=True)
        
        data.return_value = os_codenames, salt_versions, ceph_versions
        ret = status.report(return_data=True)

        for ident in ['salt', 'ceph', 'os']:
            assert ret['statusreport'][0][ident] == self.versions()[ident]['old_version']
        assert ret == expect
        assert len(ret['statusreport'][1]['out of sync'].keys()) == 4

    @patch('srv.modules.runners.status._get_data')
    def test_report_6_of_9(self, data):
        """

        6 are off, 3 are in sync
        which means that common values 
        will be the old_versions

        salt: 2015.0.1
        os: SLE12SP2
        ceph_versions: ceph version 10.0.2

        Expecting to have 3 nodes in the out of sync list
        """

        salt_versions, os_codenames, ceph_versions, expect = self.alter_input(recurrence=3, reverse=True)
        
        data.return_value = os_codenames, salt_versions, ceph_versions
        ret = status.report(return_data=True)

        for ident in ['salt', 'ceph', 'os']:
            assert ret['statusreport'][0][ident] == self.versions()[ident]['old_version']
        assert ret == expect
        assert len(ret['statusreport'][1]['out of sync'].keys()) == 3

    @patch('srv.modules.runners.status._get_data')
    def test_report_9_of_9(self, data):
        """

        9 are off, 0 are in sync
        which means that common values 
        will be the old_versions

        salt: 2015.0.1
        os: SLE12SP2
        ceph_versions: ceph version 10.0.2

        Expecting to have 0 nodes in the out of sync list
        """

        salt_versions, os_codenames, ceph_versions, expect = self.alter_input(recurrence=0, reverse=True)
        
        data.return_value = os_codenames, salt_versions, ceph_versions
        ret = status.report(return_data=True)

        for ident in ['salt', 'ceph', 'os']:
            assert ret['statusreport'][0][ident] == self.versions()[ident]['old_version']
        assert ret == expect
        assert len(ret['statusreport'][1]['out of sync'].keys()) == 0
