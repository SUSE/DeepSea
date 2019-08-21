import pytest
import os
from pyfakefs import fake_filesystem, fake_filesystem_glob

from mock import patch, MagicMock
import mock
from srv.salt._modules import purge

fs = fake_filesystem.FakeFilesystem()
f_glob = fake_filesystem_glob.FakeGlobModule(fs)
f_os = fake_filesystem.FakeOsModule(fs)
f_open = fake_filesystem.FakeFileOpen(fs)

class TestPurge():

    @patch('os.path.isfile', new=f_os.path.isfile)
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('__builtin__.open', new=f_open)
    @patch('glob.glob', new=f_glob.glob)
    def test_igw_config_removed(self):

        filename = '/srv/pillar/ceph/stack/ceph/cluster.yml'
        fs.CreateFile(filename, contents='''igw_config: default-ui\n''')
        purge.igw_config()
        with open(filename, 'r') as cluster:
            contents = cluster.read().rstrip('\n')

        fs.RemoveFile(filename)
        assert contents == '{}'

    @patch('os.path.isfile', new=f_os.path.isfile)
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('__builtin__.open', new=f_open)
    @patch('glob.glob', new=f_glob.glob)
    def test_igw_config_absent(self):

        filename = '/srv/pillar/ceph/stack/ceph/cluster.yml'
        fs.CreateFile(filename, contents='''abc: def\n''')
        purge.igw_config()
        with open(filename, 'r') as cluster:
            contents = cluster.read().rstrip('\n')
        fs.RemoveFile(filename)

        assert contents == 'abc: def'

