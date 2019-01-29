import pytest
import sys
sys.path.insert(0, 'srv/salt/_modules')
from srv.salt._modules import cephdisks, helper
from tests.unit.helper.output import OutputHelper
from tests.unit.helper.fixtures import helper_specs


@pytest.mark.skip(reason="Test me")
def test_dummy():
    """ Placeholder to remind me to write tests"""
    assert False
