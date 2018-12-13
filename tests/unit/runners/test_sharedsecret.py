# -*- coding: utf-8 -*-
'''
Unit tests for the sharedsecret salt runner
'''
from pyfakefs import fake_filesystem
from mock import patch
from srv.modules.runners import sharedsecret


fs = fake_filesystem.FakeFilesystem()
f_os = fake_filesystem.FakeOsModule(fs)
f_open = fake_filesystem.FakeFileOpen(fs)


class TestSharedSecret(object):

    @patch('os.path.exists', new=f_os.path.exists)
    def test_no_sharedsecret_file(self):
        assert sharedsecret.show() is None

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    def test_valid_sharedsecret_file(self):
        fs.CreateFile('/etc/salt/master.d/sharedsecret.conf',
                      contents='sharedsecret: my-precious-key')
        key = sharedsecret.show()
        fs.RemoveFile('/etc/salt/master.d/sharedsecret.conf')
        assert key == 'my-precious-key'

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    def test_invalid_sharedsecret_file(self):
        fs.CreateFile('/etc/salt/master.d/sharedsecret.conf',
                      contents='sharedsecret = my-precious-key')
        key = sharedsecret.show()
        fs.RemoveFile('/etc/salt/master.d/sharedsecret.conf')
        assert key is None
