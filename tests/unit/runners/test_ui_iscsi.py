import pytest
import salt.client
import os
from pyfakefs import fake_filesystem, fake_filesystem_glob

from mock import patch, MagicMock
from srv.modules.runners import ui_iscsi

fs = fake_filesystem.FakeFilesystem()
f_glob = fake_filesystem_glob.FakeGlobModule(fs)
f_os = fake_filesystem.FakeOsModule(fs)
f_open = fake_filesystem.FakeFileOpen(fs)

class TestIscsi():

    @patch('salt.client.LocalClient', autospec=True)
    @patch('srv.modules.runners.ui_iscsi.Iscsi.config', autospec=True)
    @patch('srv.modules.runners.ui_iscsi.Iscsi.interfaces', autospec=True)
    @patch('srv.modules.runners.ui_iscsi.Iscsi.images', autospec=True)
    def test_populate(self, localclient, config, interfaces, images):
        iscsi = ui_iscsi.Iscsi()
        result = iscsi.populate()
        assert (config.call_count == 1 and 'config' in result and
                interfaces.call_count == 1 and 'interfaces' in result and
                images.call_count == 1 and 'images' in result)
        
    @patch('salt.client.LocalClient', autospec=True)
    def test_interfaces(self, localclient):
        expected = [{'node': 'igw1.ceph', 'addr': '172.16.11.16'}, 
                    {'node': 'igw2.ceph', 'addr': '172.16.11.17'}, 
                    {'node': 'igw3.ceph', 'addr': '172.16.11.18'}]

        local = localclient.return_value
        local.cmd.return_value = { 'igw2.ceph': ['127.0.0.1', '172.16.11.17'],
                                   'igw1.ceph': ['127.0.0.1', '172.16.11.16'],
                                   'igw3.ceph': ['127.0.0.1', '172.16.11.18'] }

        iscsi = ui_iscsi.Iscsi()
        result = iscsi.interfaces()
        assert sorted(result) == expected
 
    @patch('salt.client.LocalClient', autospec=True)
    def test_interfaces_unwrapped(self, localclient):
        expected = {'igw2.ceph': ['172.16.11.17'], 'igw1.ceph': ['172.16.11.16'], 'igw3.ceph': ['172.16.11.18']}

        local = localclient.return_value
        local.cmd.return_value = { 'igw2.ceph': ['127.0.0.1', '172.16.11.17'],
                                   'igw1.ceph': ['127.0.0.1', '172.16.11.16'],
                                   'igw3.ceph': ['127.0.0.1', '172.16.11.18'] }

        iscsi = ui_iscsi.Iscsi()
        result = iscsi.interfaces(wrapped=False)
        assert result == expected
 
    @patch('salt.config.client_config', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    @patch('salt.utils.minions.mine_get', autospec=True)
    def test_images(self, mine_get, localclient, client_config):
        expected = [{'pool': 'rbd', 'img': ['demo']}]

        mine_get.return_value = {'admin': {'rbd': ['demo']}}

        iscsi = ui_iscsi.Iscsi()
        result = iscsi.images()

        assert result == expected
 
    @patch('salt.config.client_config', autospec=True)
    @patch('salt.client.LocalClient', autospec=True)
    @patch('salt.utils.minions.mine_get', autospec=True)
    def test_images_unwrapped(self, mine_get, localclient, client_config):
        expected = {'rbd': ['demo']}

        mine_get.return_value = {'admin': {'rbd': ['demo']}}

        iscsi = ui_iscsi.Iscsi()
        result = iscsi.images(wrapped=False)

        assert result == expected
 
    @patch('salt.client.LocalClient', autospec=True)
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('__builtin__.open', new=f_open)
    def test_config(self, localclient):

        fs.CreateFile('/srv/salt/ceph/igw/cache/lrbd.conf', contents='{}')
        iscsi = ui_iscsi.Iscsi()
        result = iscsi.config()
        fs.RemoveFile('/srv/salt/ceph/igw/cache/lrbd.conf')
        assert result == {}

    @patch('salt.client.LocalClient', autospec=True)
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('__builtin__.open', new=f_open)
    def test_config_missing(self, localclient):

        iscsi = ui_iscsi.Iscsi()
        result = iscsi.config()
        assert result == None

    @patch('salt.client.LocalClient', autospec=True)
    @patch('srv.modules.runners.ui_iscsi.Iscsi._set_igw_config', autospec=True)
    @patch('__builtin__.open', new=f_open)
    def test_save(self, localclient, set_igw_config):

        iscsi = ui_iscsi.Iscsi()
        iscsi.save(data='hello')
        with open('/srv/salt/ceph/igw/cache/lrbd.conf', 'r') as config:
            results = config.read()
        assert results == 'hello'

    @patch('salt.client.LocalClient', autospec=True)
    @patch('__builtin__.open', new=f_open)
    def test_set_igw_config(self, localclient):
        fs.CreateFile('/srv/pillar/ceph/stack/ceph/cluster.yml', contents='')

        iscsi = ui_iscsi.Iscsi()
        iscsi._set_igw_config()
        with open('/srv/pillar/ceph/stack/ceph/cluster.yml', 'r') as config:
            results = config.read()
        assert results.strip() == 'igw_config: default-ui'

