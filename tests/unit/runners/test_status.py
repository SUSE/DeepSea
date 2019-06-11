from mock import patch
import pytest
from srv.modules.runners import status
from tests.unit.helper.output import OutputHelper
import six


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
                for node,value in six.iteritems(data):
                    data[node] = data[node].replace(ov, cv)

            for count, (node, value) in enumerate(six.iteritems(data), 0):
                if count < recurrence:
                    data[node] = ov
                    if node not in expect['statusreport'][1]['out of sync']:
                        expect['statusreport'][1]['out of sync'].update({node: {}})
                    expect['statusreport'][1]['out of sync'][node].update({key: ov})

        return salt_versions, os_codenames, ceph_versions, expect

    @pytest.mark.parametrize('off, in_sync, expect_version', [
        (0, 9, 'common_version'),
        # 0 are off, all are in sync
        # Expecting to have the Common Version to be 'common_version'
        # Expecting to have 0 nodes in the out of sync list

        (1, 8, 'common_version'),
        # 1 are off, 8 are in sync
        # Expecting to have the Common Version to be 'common_version'
        # Expecting to have 1 nodes in the out of sync list

        (3, 6, 'common_version'),
        # 3 are off, 6 are in sync
        # Expecting to have the Common Version to be 'common_version'
        # Expecting to have 3 nodes in the out of sync list

        (4, 5, 'common_version'),
        # 4 are off, 5 are in sync
        # Expecting to have the Common Version to be 'common_version'
        # Expecting to have 4 nodes in the out of sync list

        (5, 4, 'old_version'),
        # 5 are off, 4 are in sync
        # which means that common values will be the 'old_version'

        # Expecting to have 4 nodes in the out of sync list

        (6, 3, 'old_version'),
        # 6 are off, 3 are in sync
        # which means that common values will be the 'old_version'
        # Expecting to have 3 nodes in the out of sync list

        (9, 0, 'old_version'),
        # 9 are off, 0 are in sync
        # which means that common values will be the 'old_version'
        # Expecting to have 0 nodes in the out of sync list
    ])
    @patch('srv.modules.runners.status._get_data')
    def test_report(self, data, off, in_sync, expect_version):
        reverse = off > in_sync
        out_of_sync = recurrence = min(off, in_sync)
        salt_versions, os_codenames, ceph_versions, expect = self.alter_input(recurrence, reverse)

        data.return_value = os_codenames, salt_versions, ceph_versions
        ret = status.report(return_data=True)

        for ident in ['salt', 'ceph', 'os']:
            assert ret['statusreport'][0][ident] == self.versions()[ident][expect_version]
        assert ret == expect
        assert len(ret['statusreport'][1]['out of sync'].keys()) == out_of_sync
