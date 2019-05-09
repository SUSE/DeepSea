from mock import patch
from srv.modules.runners import deepsea


class TestVersion():
    """
    A class for validating how DeepSea reports its version
    """

    @patch('srv.modules.runners.deepsea.DEEPSEA_VERSION', 'something wildly unexpected')
    def test_version_1(self):
        result = deepsea.version(format='json')
        assert result['full_version'] == 'something wildly unexpected'
        assert result['version'] == '0.0.0'

    @patch('srv.modules.runners.deepsea.DEEPSEA_VERSION', '0.8.10+git.0.72e3fed70')
    def test_version_2(self):
        result = deepsea.version(format='json')
        assert result['full_version'] == '0.8.10+git.0.72e3fed70'
        assert result['version'] == '0.8.10'

    @patch('srv.modules.runners.deepsea.DEEPSEA_VERSION', '0.82+git.0.72e3fed70')
    def test_version_3(self):
        result = deepsea.version(format='json')
        assert result['full_version'] == '0.82+git.0.72e3fed70'
        assert result['version'] == '0.82'

    @patch('srv.modules.runners.deepsea.DEEPSEA_VERSION', '1.2.3.4.5.6+git.0.72e3fed70')
    def test_version_4(self):
        result = deepsea.version(format='json')
        assert result['full_version'] == '1.2.3.4.5.6+git.0.72e3fed70'
        assert result['version'] == '1.2.3.4.5.6'

    @patch('srv.modules.runners.deepsea.DEEPSEA_VERSION', '110.220.3330.44.52+git.0.72e3fed70')
    def test_version_5(self):
        result = deepsea.version(format='json')
        assert result['full_version'] == '110.220.3330.44.52+git.0.72e3fed70'
        assert result['version'] == '110.220.3330.44.52'
