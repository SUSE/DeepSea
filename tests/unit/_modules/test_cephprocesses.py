import pytest
from srv.salt._modules import cephprocesses

from mock import patch, MagicMock

@patch('pwd.getpwnam')
def test_process_map(mock_pwd):
    mock_pwd.side_effect = KeyError()
    result = cephprocesses._process_map()
    assert result == []

