import pytest
import salt.client
import os
import sys
sys.path.insert(0, 'srv/salt/_modules')
##from pyfakefs import fake_filesystem, fake_filesystem_glob
from mock import patch, MagicMock, mock
from srv.salt._modules import public

#fs = fake_filesystem.FakeFilesystem()
#f_glob = fake_filesystem_glob.FakeGlobModule(fs)
#f_os = fake_filesystem.FakeOsModule(fs)
#f_open = fake_filesystem.FakeFileOpen(fs)

class Testpublic():

    def test_address_missing_public_network(self):
        public.__pillar__ = {}
        result = public.address()
        assert result == ""

    def test_address_empty_public_network(self):
        public.__pillar__ = {'public_network': ''}
        public.__salt__ = {}
        public.__salt__['network.interfaces'] = mock.Mock()
        public.__salt__['network.interfaces'].return_value = {}
        result = public.address()
        assert result == ""

    def test_address_public_network_ipv4(self):
        public.__pillar__ = {'public_network': '192.168.0.0/24'}
        public.__salt__ = {}
        public.__salt__['network.interfaces'] = mock.Mock()
        public.__salt__['network.interfaces'].return_value = {'eth0': {
          'inet': [{'address': '192.168.0.102'}],
          'inet6': [{'address': 'fd00::102'}]
        }}

        result = public.address()
        assert result == "192.168.0.102"

    def test_address_public_network_ipv6(self):
        public.__pillar__ = {'public_network': 'fd00::/64'}
        public.__salt__ = {}
        public.__salt__['network.interfaces'] = mock.Mock()
        public.__salt__['network.interfaces'].return_value = {'eth0': {
          'inet': [{'address': '192.168.0.102'}],
          'inet6': [{'address': 'fd00::102'}]
        }}

        result = public.address()
        assert result == "fd00::102"

