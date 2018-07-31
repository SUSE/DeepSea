import pytest
import salt.client
import os
from pyfakefs import fake_filesystem, fake_filesystem_glob

from mock import patch, MagicMock
import mock
from srv.modules.runners import ui_rgw

fs = fake_filesystem.FakeFilesystem()
f_glob = fake_filesystem_glob.FakeGlobModule(fs)
f_os = fake_filesystem.FakeOsModule(fs)
f_open = fake_filesystem.FakeFileOpen(fs)

class TestRadosgw():

    @patch('salt.client.LocalClient', autospec=True)
    @patch('salt.utils.master.MasterPillarUtil', autospec=True)
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('__builtin__.open', new=f_open)
    @patch('glob.glob', new=f_glob.glob)
    def test_admin(self, masterpillarutil, localclient):
        result = {'urls': [],
                  'access_key': '12345',
                  'secret_key': 'abcdef',
                  'user_id': 'admin',
                  'success': True}

        fs.CreateFile('cache/user.admin.json',
                      contents='''{\n"keys": [\n{\n"user": "admin",\n"access_key": "12345",\n"secret_key": "abcdef"\n}\n]\n}''')
        rg = ui_rgw.Radosgw(pathname="cache")
        fs.RemoveFile('cache/user.admin.json')

        assert result == rg.credentials

    @patch('salt.client.LocalClient', autospec=True)
    @patch('salt.utils.master.MasterPillarUtil', autospec=True)
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('__builtin__.open', new=f_open)
    @patch('glob.glob', new=f_glob.glob)
    def test_admin_system_user(self, masterpillarutil, localclient):
        result = {'urls': [],
                  'access_key': '12345',
                  'secret_key': 'abcdef',
                  'user_id': 'jdoe',
                  'success': True}

        fs.CreateFile('cache/user.jdoe.json',
                      contents='''{\n"system": "true",\n"keys": [\n{\n"user": "jdoe",\n"access_key": "12345",\n"secret_key": "abcdef"\n}\n]\n}''')
        rg = ui_rgw.Radosgw(pathname="cache")
        fs.RemoveFile('cache/user.jdoe.json')

        assert result == rg.credentials

    @patch('salt.client.LocalClient', autospec=True)
    @patch('salt.utils.master.MasterPillarUtil', autospec=True)
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('__builtin__.open', new=f_open)
    @patch('glob.glob', new=f_glob.glob)
    def test_admin_no_system_user(self, masterpillarutil, localclient):
        result = {'urls': [],
                  'access_key': None,
                  'secret_key': None,
                  'user_id': None,
                  'success': False}

        fs.CreateFile('cache/user.jdoe.json',
                      contents='''{\n"keys": [\n{\n"user": "jdoe",\n"access_key": "12345",\n"secret_key": "abcdef"\n}\n]\n}''')
        rg = ui_rgw.Radosgw(pathname="cache")
        fs.RemoveFile('cache/user.jdoe.json')

        assert result == rg.credentials

    @patch('salt.client.LocalClient', autospec=True)
    @patch('salt.utils.master.MasterPillarUtil', autospec=True)
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('__builtin__.open', new=f_open)
    @patch('glob.glob', new=f_glob.glob)
    def test_admin_disabled_system_user(self, masterpillarutil, localclient):
        result = {'urls': [],
                  'access_key': None,
                  'secret_key': None,
                  'user_id': None,
                  'success': False}

        fs.CreateFile('cache/user.jdoe.json',
                      contents='''{\n"system": "false",\n"keys": [\n{\n"user": "jdoe",\n"access_key": "12345",\n"secret_key": "abcdef"\n}\n]\n}''')
        rg = ui_rgw.Radosgw(pathname="cache")
        fs.RemoveFile('cache/user.jdoe.json')

        assert result == rg.credentials

