import pytest
from srv.salt._modules import kernel
from mock import patch, MagicMock

def test_boot_image():
    data = 'BOOT_IMAGE=/boot/vmlinuz-4.1.12-1-default'
    result = kernel._boot_image(data)
    assert result == '/boot/vmlinuz-4.1.12-1-default'

@patch('os.path.isfile')
def test_query_command_succeeds(mock_isfile):
    mock_isfile.return_value = True
    result = kernel._query_command("afile")
    assert result == ['/bin/rpm', '-qf', 'afile']

@patch('os.path.isfile')
def test_query_command_fails(mock_isfile):
    mock_isfile.return_value = False
    result = kernel._query_command("afile")
    assert result == None

@patch('os.path.isfile')
def test_query_command_fails_with_no_file(mock_isfile):
    mock_isfile.return_value = True
    result = kernel._query_command("")
    assert result == None

