import sys
sys.path.insert(0, 'srv/modules/pillar')

import pytest
from srv.modules.runners import cluster


class TestClusterName():
    def test_name_ceph_namespace(self):
        cluster.__pillar__ = {'ceph': {'cluster': 'some_name'}}
        assert cluster.name() == 'some_name'

    def test_name_original_namespace(self):
        cluster.__pillar__ = {'cluster': 'some_other_name'}
        assert cluster.name() == 'some_other_name'

    def test_name_default_namespace(self):
        cluster.__pillar__ = {'some_random': 'some_other_name'}
        assert cluster.name() == 'ceph'
