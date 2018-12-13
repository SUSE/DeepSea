import pytest
import salt.client
import os
import sys
sys.path.insert(0, 'srv/salt/_modules')
from pyfakefs import fake_filesystem, fake_filesystem_glob
from mock import patch, MagicMock
from srv.salt._modules import rgw

fs = fake_filesystem.FakeFilesystem()
f_glob = fake_filesystem_glob.FakeGlobModule(fs)
f_os = fake_filesystem.FakeOsModule(fs)
f_open = fake_filesystem.FakeFileOpen(fs)

class TestRadosgw():

    @patch('salt.client.LocalClient', autospec=True)
    @patch('os.path.isfile', new=f_os.path.isfile)
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('salt.config.client_config', autospec=True)
    @patch('salt.utils.master.MasterPillarUtil', autospec=True)
    @patch('builtins.open', new=f_open)
    @patch('glob.glob', new=f_glob.glob)
    def test_urls_dedicated_node(self, masterpillarutil, config, localclient):
        expected = {'url': "http://rgw1:7480/admin",
                    'ssl': False,
                    'port': '7480',
                    'host': 'rgw1' }

        localclient().cmd.return_value = {
            'rgw1': {
                'fqdn': 'rgw1'
            }
        }

        fs.CreateFile('cache/client.rgw.rgw1.json',
                      contents='''[client.rgw.rgw1]\nkey = 12345\ncaps mon = "allow rwx"\ncaps osd = "allow rwx"\n''')
        fs.CreateFile('/srv/salt/ceph/configuration/files/rgw.conf',
                      contents='''[client.rgw.rgw1]\nkey = 12345\ncaps mon = "allow rwx"\ncaps osd = "allow rwx"\n''')

        result = rgw.endpoints()[0]
        fs.RemoveFile('cache/client.rgw.rgw1.json')
        fs.RemoveFile('/srv/salt/ceph/configuration/files/rgw.conf')

        assert expected == result

    @patch('salt.client.LocalClient', autospec=True)
    @patch('os.path.isfile', new=f_os.path.isfile)
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('salt.config.client_config', autospec=True)
    @patch('salt.utils.master.MasterPillarUtil', autospec=True)
    @patch('builtins.open', new=f_open)
    @patch('glob.glob', new=f_glob.glob)
    def test_urls_dedicated_node_with_ssl(self, masterpillarutil, config, localclient):
        expected = {'url': "https://rgw1:443/admin",
                    'ssl': True,
                    'port': 443,
                    'host': 'rgw1' }

        localclient().cmd.return_value = {
            'rgw1': {
                'fqdn': 'rgw1'
            }
        }

        fs.CreateFile('cache/client.rgw.rgw1.json')
        fs.CreateFile('/srv/salt/ceph/configuration/files/rgw.conf',
                      contents='''[client.rgw.rgw1]\nrgw_frontends = civetweb port=443s ssl_certificate=/etc/ceph/private/keyandcert.pem\nkey = 12345\ncaps mon = "allow rwx"\ncaps osd = "allow rwx"\n''')

        result = rgw.endpoints()[0]
        fs.RemoveFile('cache/client.rgw.rgw1.json')
        fs.RemoveFile('/srv/salt/ceph/configuration/files/rgw.conf')

        assert expected == result

    @patch('salt.client.LocalClient', autospec=True)
    @patch('os.path.isfile', new=f_os.path.isfile)
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('salt.config.client_config', autospec=True)
    @patch('salt.utils.master.MasterPillarUtil', autospec=True)
    @patch('builtins.open', new=f_open)
    @patch('glob.glob', new=f_glob.glob)
    def test_urls_dedicated_node_with_admin_entry(self, masterpillarutil, config, localclient):
        expected = {'url': "https://rgw1:443/sys",
                    'ssl': True,
                    'port': 443,
                    'host': 'rgw1' }

        localclient().cmd.return_value = {
            'rgw1': {
                'fqdn': 'rgw1'
            }
        }

        fs.CreateFile('cache/client.rgw.rgw1.json')
        fs.CreateFile('/srv/salt/ceph/configuration/files/rgw.conf',
                      contents='''[client.rgw.rgw1]\nrgw_frontends = civetweb port=443s\nkey = 12345\ncaps mon = "allow rwx"\ncaps osd = "allow rwx"\nrgw admin entry = sys\n''')

        result = rgw.endpoints()[0]
        fs.RemoveFile('cache/client.rgw.rgw1.json')
        fs.RemoveFile('/srv/salt/ceph/configuration/files/rgw.conf')

        assert expected == result

    @patch('salt.client.LocalClient', autospec=True)
    @patch('os.path.isfile', new=f_os.path.isfile)
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('salt.config.client_config', autospec=True)
    @patch('salt.utils.master.MasterPillarUtil', autospec=True)
    @patch('builtins.open', new=f_open)
    @patch('glob.glob', new=f_glob.glob)
    def test_urls_shared_node(self, masterpillarutil, config, localclient):
        expected = {'url': "http://rgw:7480/admin",
                    'ssl': False,
                    'port': '7480',
                    'host': 'rgw' }

        localclient().cmd.return_value = {
            'rgw1': {
                'fqdn': 'rgw'
            }
        }

        fs.CreateFile('cache/client.rgw.json',
                      contents='''[client.rgw]\nkey = 12345\ncaps mon = "allow rwx"\ncaps osd = "allow rwx"\n''')
        fs.CreateFile('/srv/salt/ceph/configuration/files/rgw.conf',
                      contents='''[client.rgw.rgw1]\nkey = 12345\ncaps mon = "allow rwx"\ncaps osd = "allow rwx"\n''')

        result = rgw.endpoints()[0]
        fs.RemoveFile('cache/client.rgw.json')
        fs.RemoveFile('/srv/salt/ceph/configuration/files/rgw.conf')

        assert expected == result

    @patch('salt.client.LocalClient', autospec=True)
    @patch('os.path.isfile', new=f_os.path.isfile)
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('salt.config.client_config', autospec=True)
    @patch('salt.utils.master.MasterPillarUtil', autospec=True)
    @patch('builtins.open', new=f_open)
    @patch('glob.glob', new=f_glob.glob)
    def test_urls_shared_node_with_ssl(self, masterpillarutil, config, localclient):
        expected = {'url': "https://rgw:443/admin",
                    'ssl': True,
                    'port': 443,
                    'host': 'rgw' }

        localclient().cmd.return_value = {
            'rgw1': {
                'fqdn': 'rgw'
            }
        }

        fs.CreateFile('cache/client.rgw.json')
        fs.CreateFile('/srv/salt/ceph/configuration/files/rgw.conf',
                      contents='''[client.rgw.rgw1]\nrgw_frontends = civetweb port=443s ssl_certificate=/etc/ceph/private/keyandcert.pem\nkey = 12345\ncaps mon = "allow rwx"\ncaps osd = "allow rwx"\n''')

        result = rgw.endpoints()[0]
        fs.RemoveFile('cache/client.rgw.json')
        fs.RemoveFile('/srv/salt/ceph/configuration/files/rgw.conf')

        assert expected == result


    @patch('salt.client.LocalClient', autospec=True)
    @patch('salt.config.client_config', autospec=True)
    @patch('salt.utils.master.MasterPillarUtil', autospec=True)
    @patch('builtins.open', new=f_open)
    @patch('glob.glob', new=f_glob.glob)
    def test_urls_endpoint_defined(self, masterpillarutil, config, localclient):
        expected = {'url': "http://abc.def/admin",
                    'ssl': False,
                    'port': 7480,
                    'host': 'abc.def/admin' }

        mpu = masterpillarutil.return_value
        mpu.get_minion_pillar.return_value = { "minionA": { "rgw_endpoint": "http://abc.def/admin" }}
        result = rgw.endpoints()[0]

        assert expected == result
