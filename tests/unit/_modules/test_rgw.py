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

    pass
