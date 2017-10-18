from pyfakefs import fake_filesystem as fake_fs
from pyfakefs import fake_filesystem_glob as fake_glob
from mock import patch, mock_open, MagicMock
from srv.modules.runners import push

fs = fake_fs.FakeFilesystem()
proposal_dir = '/srv/pillar/ceph/proposals/cluster-ceph/cluster'
nodes = [
        'master',
        'mon1',
        'mon2',
        'mon3',
        'mds1',
        'mds2',
        'osd1',
        'osd2',
        'osd3',
        'osd4',
        'osd5',
        'rgw1',
        ]

for node in nodes:
    fs.CreateFile('{}/{}.sls'.format(proposal_dir,
                                     node))
fs.CreateFile('policy.cfg', contents='cluster-ceph/cluster/*.sls')
fs.CreateFile('policy.cfg_commented1',
              contents='cluster-ceph/cluster/*.sls # with a comment')
fs.CreateFile('policy.cfg_commented2',
              contents='cluster-ceph/cluster/*.sls \t# with a comment')
fs.CreateFile('policy.cfg_ml_commented',
              contents=('# a line comment\n'
                        'cluster-ceph/cluster/*.sls \t# with a comment'))
fs.CreateFile('policy.cfg_leading_whitespace',
              contents=(' cluster-ceph/cluster/*.sls'))
fs.CreateFile('policy.cfg_trailing_whitespace',
              contents=('cluster-ceph/cluster/*.sls '))
fs.CreateFile('policy.cfg_trailing_and_leading_whitespace',
              contents=(' cluster-ceph/cluster/*.sls '))
fs.CreateFile('policy.cfg_trailing_and_leading_whitespace_and_leading_comment',
              contents=(' #cluster-ceph/cluster/*.sls '))
fs.CreateFile('policy.cfg_trailing_and_leading_whitespace_and_trailing_comment',
              contents=(' cluster-ceph/cluster/*.sls #'))

f_glob = fake_glob.FakeGlobModule(fs)
f_os = fake_fs.FakeOsModule(fs)
f_open = fake_fs.FakeFileOpen(fs)


class TestPush():

    @patch('glob.glob', new=f_glob.glob)
    def test_parse(self):

        parsed = push._parse('{}/*.sls'.format(proposal_dir))
        assert len(parsed) == len(nodes)

        parsed = push._parse('{}/mon*.sls'.format(proposal_dir))
        assert len(parsed) == len([n for n in nodes if n.startswith('mon')])

        parsed = push._parse('{}/mon[1,2].sls'.format(proposal_dir))
        assert len(parsed) == 2

        parsed = push._parse('{}/*.sls slice=[2:5]'.format(proposal_dir))
        assert len(parsed) == 3

        parsed = push._parse('{}/*.sls re=.*1\.sls$'.format(proposal_dir))
        assert len(parsed) == len([n for n in nodes if '1' in n])

        parsed = push._parse('{}/*.sls FOO=.*1\.sls$'.format(proposal_dir))
        assert len(parsed) == len(nodes)

    @patch('glob.glob', new=f_glob.glob)
    @patch('os.path.isfile', new=f_os.path.isfile)
    @patch('__builtin__.open', new=f_open)
    @patch('os.stat')
    def test_organize(self, mock_stat):
        # make sure all out faked files have content
        mock_stat.return_value = MagicMock(st_size=1)
        p_d = push.PillarData(False)

        organized = p_d.organize('policy.cfg')
        assert len(organized.keys()) == len(nodes)

        organized = p_d.organize('policy.cfg_commented1')
        assert len(organized.keys()) == len(nodes)

        organized = p_d.organize('policy.cfg_commented2')
        assert len(organized.keys()) == len(nodes)

        organized = p_d.organize('policy.cfg_ml_commented')
        assert len(organized.keys()) == len(nodes)

        organized = p_d.organize('policy.cfg_leading_whitespace')
        assert len(organized.keys()) == len(nodes)

        organized = p_d.organize('policy.cfg_trailing_whitespace')
        assert len(organized.keys()) == len(nodes)

        organized = p_d.organize('policy.cfg_trailing_and_leading_whitespace')
        assert len(organized.keys()) == len(nodes)

        organized = p_d.organize('policy.cfg_trailing_and_leading_whitespace_and_leading_comment')
        assert len(organized.keys()) == 0

        organized = p_d.organize('policy.cfg_trailing_and_leading_whitespace_and_trailing_comment')
        assert len(organized.keys()) == len(nodes)
