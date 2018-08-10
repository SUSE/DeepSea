from srv.modules.runners import proposal
import pytest
from mock import patch, mock_open, call
import sys
from collections import namedtuple
sys.path.insert(0, 'srv/modules/pillar')


@pytest.fixture
def minions():
    ToReplace = namedtuple('ToReplace', ['fullpath', 'filename'])
    return {
            'minion1': {
                'minion': ToReplace('/srv/pillar/ceph/proposals/profile-default/stack/default/ceph/minions/data1.ceph.yml-replace', 'data1.ceph.yml-replace'),
                'basepath': "/srv/pillar/ceph/proposals/profile-default/stack/default/ceph/minions/data1.ceph.yml",
                'basename': "data1.ceph.yml",
                'name':     "data1.ceph",
                'num_replace': 2,
                'disks': [
                    {'Device File': '/dev/vdc', 'Noise': True},
                    {'Device File': '/dev/vdb', 'Noise': True},
                    {'Device File': '/dev/vdd', 'Noise': True}
                ],
                'osds': {
                    '/dev/vdb': {'format': 'bluestore', 'replace': False, 'old': 'vdb'},
                    '/dev/vdd': {'format': 'bluestore', 'replace': True, 'old': 'vdd'},
                    '/dev/vdc': {'format': 'bluestore', 'replace': True, 'old': 'vdc'}
                },
                'expected': { 'ceph': {'storage': {'osds': {
                    '/dev/vdb': {'format': 'bluestore', 'old': 'vdb'},
                    '/dev/vdc': {'format': 'bluestore', 'old': 'vdc'},
                    '/dev/vdd': {'format': 'bluestore', 'old': 'vdd'}}}}}
            },
            'minion2': {
                'minion': ToReplace('/srv/pillar/ceph/proposal/profile-alternative/stack/default/minions/data2.ceph.yml-replace', 'data2.ceph.yml-replace'),
                'basepath': "/srv/pillar/ceph/proposal/profile-alternative/stack/default/minions/data2.ceph.yml",
                'basename': "data2.ceph.yml",
                'name':     "data2.ceph",
                'num_replace': 2,
                'disks': [
                    {'Device File': '/dev/vdc', 'Noise': True},
                    {'Device File': '/dev/vdb', 'Noise': True},
                    {'Device File': '/dev/vde', 'Noise': True},
                    {'Device File': '/dev/vdf', 'Noise': True}
                ],
                'osds': {
                    '/dev/vdb': {'format': 'bluestore', 'old': 'vdb'},
                    '/dev/vdd': {'format': 'bluestore', 'replace': True, 'old': 'vdd'},
                    '/dev/vdc': {'format': 'bluestore', 'replace': True, 'old': 'vdc'},
                    '/dev/vde': {'format': 'bluestore', 'old': 'vde'}},
                'expected': { 'ceph': {'storage': {'osds': {
                    '/dev/vdb': {'format': 'bluestore', 'old': 'vdb'},
                    '/dev/vdc': {'format': 'bluestore', 'old': 'vdc'},
                    '/dev/vde': {'format': 'bluestore', 'old': 'vde'},
                    '/dev/vdf': {'format': 'bluestore', 'old': 'vdd'}}}}}
                },
            'minion3': {
                'minion': ToReplace('/srv/pillar/ceph/proposal/profile-default/stack/default/minions/data3.ceph.yml', 'data3.ceph.yml'),
                'basepath': "/srv/pillar/ceph/proposal/profile-default/stack/default/minions/data3.ceph.yml",
                'basename': "data3.ceph.yml",
                'name':     "data3.ceph",
                'num_replace': 1,
                'disks': [
                    {'Device File': '/dev/vdb', 'Noise': True},
                    {'Device File': '/dev/vde', 'Noise': True}
                ],
                'osds': {
                    '/dev/vdc': {'format': 'bluestore', 'old': 'vdc', 'replace': True},
                    '/dev/vde': {'format': 'bluestore', 'old': 'vde'}},
                'expected': { 'ceph': {'storage': {'osds': {
                    '/dev/vdb': {'format': 'bluestore', 'old': 'vdc'},
                    '/dev/vde': {'format': 'bluestore', 'old': 'vde'}}}}}
                },
            'minion4': {
                'minion': ToReplace('/srv/pillar/ceph/proposal/profile-default/stack/default/minions/we.use.a-very?weird-naming.scheme/node.yml-replace', 'node.yml-replace'),
                'basepath': "/srv/pillar/ceph/proposal/profile-default/stack/default/minions/we.use.a-very?weird-naming.scheme/node.yml",
                'basename': "node.yml",
                'name':     "node",
                'num_replace': 0,
                'disks': [
                    {'Device File': '/dev/vdb', 'Noise': True},
                    {'Device File': '/dev/vdc', 'Noise': True},
                    {'Device File': '/dev/vdd', 'Noise': True},
                    {'Device File': '/dev/vdf', 'Noise': True}
                ],
                'osds': {
                    '/dev/vdb': {'format': 'bluestore', 'old': 'vdb'},
                    '/dev/vdc': {'format': 'bluestore', 'old': 'vdc'},
                    '/dev/vdd': {'format': 'bluestore', 'old': 'vdd'},
                    '/dev/vdf': {'format': 'bluestore', 'old': 'vdf'}},
                'expected': { 'ceph': {'storage': {'osds': {
                    '/dev/vdb': {'format': 'bluestore', 'old': 'vdb'},
                    '/dev/vdc': {'format': 'bluestore', 'old': 'vdc'},
                    '/dev/vdd': {'format': 'bluestore', 'old': 'vdd'},
                    '/dev/vdf': {'format': 'bluestore', 'old': 'vdf'}}}}}
                },
            }

class TestProposalRunner(object):

    @patch('srv.modules.runners.proposal.isfile', autospec=True)
    @patch('os.listdir', autospec=True)
    def test_find_minions_to_replace(self, mock_listdir, mock_isfile):
        mock_listdir.return_value = ['data1.ceph.yml-replace']
        mock_isfile.return_value = True
        directory = '/srv/pillar/ceph/proposals/profile-default'
        result = proposal._find_minions_to_replace(directory)

        assert result[0].filename == 'data1.ceph.yml-replace'

    @patch('srv.modules.runners.proposal.isfile', autospec=True)
    @patch('os.listdir', autospec=True)
    def test_find_multiple_minions_to_replace(self, mock_listdir, mock_isfile):
        mock_listdir.return_value = ['data1.ceph.yml-replace', 'data2.ceph.yml-replace']
        mock_isfile.return_value = True
        directory = '/srv/pillar/ceph/proposals/profile-default'
        result = proposal._find_minions_to_replace(directory)

        assert result[0].filename == 'data1.ceph.yml-replace'
        assert result[1].filename == 'data2.ceph.yml-replace'

    @patch('srv.modules.runners.proposal.isfile', autospec=True)
    @patch('os.listdir', autospec=True)
    def test_find_minions_to_replace_no_result(self, mock_listdir, mock_isfile):
        mock_listdir.return_value = ['.data1.ceph.yml-replace.swp']
        mock_isfile.return_value = True
        directory = '/srv/pillar/ceph/proposals/profile-default'
        result = proposal._find_minions_to_replace(directory)

        assert not result

    class NoInitReplaceDisk(proposal.ReplaceDiskOn):
        """ Don't populate attributes via private methods automatically """

        def __init__(self, minion):
            self.minion = minion

    # range upper limit is amount of minions in fixture + 1
    @pytest.mark.parametrize("execution_number", range(1, 5))
    def test_proposal_basepath(self, execution_number, minions):
        minion = minions['minion{}'.format(execution_number)]
        RD = self.NoInitReplaceDisk(minion['minion'])

        assert RD._proposal_basepath() == minion['basepath']

    @pytest.mark.parametrize("execution_number", range(1, 5))
    def test_proposal_basename(self, execution_number, minions):
        minion = minions['minion{}'.format(execution_number)]
        RD = self.NoInitReplaceDisk(minion['minion'])

        assert RD._proposal_basename() == minion['basename']

    @pytest.mark.parametrize("execution_number", range(1, 5))
    def test_minion_name_from_file(self, execution_number, minions):
        minion = minions['minion{}'.format(execution_number)]
        RD = self.NoInitReplaceDisk(minion['minion'])
        RD.proposal_basename = minion['basename']

        assert RD._minion_name_from_file() == minion['name']

    @patch('srv.modules.runners.proposal.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_load_proposal(self, mock_yaml, mock_file, minions):
        minion = minions['minion1']['minion']
        proposal_dict = "{'fake_dict': True}"
        mock_yaml.return_value = proposal_dict
        RD = self.NoInitReplaceDisk(minion)

        assert RD._load_proposal() == proposal_dict
        mock_yaml.assert_called_once()

    @patch('salt.client.LocalClient', autospec=True)
    def test_query_node_disks(self, mock_client, minions):
        minion = minions['minion1']['minion']
        local_client = mock_client.return_value
        call1 = call('data1.ceph', 'mine.delete', ['cephdisks.list'], tgt_type='compound')
        call2 = call('data1.ceph', 'cephdisks.list', tgt_type='compound')
        RD = self.NoInitReplaceDisk(minion)
        RD.name = 'data1.ceph'

        RD._query_node_disks()

        assert local_client.cmd.call_count == 2
        assert local_client.cmd.call_args_list[0] == call1
        assert local_client.cmd.call_args_list[1] == call2

    @pytest.mark.parametrize("execution_number", range(1, 5))
    def test_strip_replace_flages(self, execution_number, minions):
        minion = minions['minion{}'.format(execution_number)]
        RD = self.NoInitReplaceDisk(minion['minion'])
        RD.proposal = {'ceph': {'storage': {'osds': minion['osds']}}}
        RD.flagged_replace = [x for x in minion['osds'] if 'replace' in minion['osds'][x]]

        RD._strip_replace_flags()

        for conf in RD.proposal['ceph']['storage']['osds'].values():
            assert 'replace' not in conf

    @pytest.mark.parametrize("execution_number", range(1, 5))
    def test_swap_disks_in_proposal(self, execution_number, minions):
        minion = minions['minion{}'.format(execution_number)]
        RD = self.NoInitReplaceDisk(minion['minion'])
        RD.proposal = {'ceph': {'storage': {'osds': minion['osds']}}}
        RD.flagged_replace = [x for x in minion['osds'] if 'replace' in minion['osds'][x]]
        RD.unused_disks = [x['Device File'] for x in minion['disks']
                           # disks in new slots
                           if x['Device File'] not in minion['osds']
                           # disks that are exchanged in place
                           or 'replace' in minion['osds'][x['Device File']]
                           and minion['osds'][x['Device File']]['replace'] is True]
        keys_to_add = RD.unused_disks[:]

        RD._swap_disks_in_proposal()

        for i in range(minion['num_replace']):
            assert keys_to_add[i] in RD.proposal['ceph']['storage']['osds']


    @pytest.mark.parametrize("execution_number", range(1, 5))
    @patch('salt.client.LocalClient')
    @patch('srv.modules.runners.proposal.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_replace(self, mock_yaml, mock_file, mock_client, execution_number, minions):
        minion = minions['minion{}'.format(execution_number)]
        mock_yaml.return_value = {'ceph': {'storage': {'osds': minion['osds']}}}

        RD = proposal.ReplaceDiskOn(minion['minion'])
        # salt client has two different returns so instead of settings its
        # return value we set the disks directly and re-run methods that depend
        # on correct disks
        RD.disks = minion['disks']
        RD.device_files = RD._extract_device_files()
        RD.unused_disks = RD._unused_disks()
        RD.replace()

        mock_yaml.assert_called()
        assert RD.proposal == minion['expected']
