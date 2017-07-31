# -*- coding: utf-8 -*-
import configobj

from pyfakefs import fake_filesystem_unittest
from mock import MagicMock, patch, mock

from srv.salt._modules import openattic
from salt.exceptions import CommandExecutionError


class TestOpenatticModule(fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_configure_salt_api(self):
        config_file = "/etc/sysconfig/openattic"
        self.fs.CreateFile(config_file, contents="")
        openattic.configure_salt_api("salt.localhost", 9000, "admin", "mysharedsecret")
        config = configobj.ConfigObj(config_file)
        self.assertEqual(config['SALT_API_HOST'], "salt.localhost")
        self.assertEqual(config['SALT_API_PORT'], "9000")
        self.assertEqual(config['SALT_API_USERNAME'], "admin")
        self.assertEqual(config['SALT_API_EAUTH'], "sharedsecret")
        self.assertEqual(config['SALT_API_SHARED_SECRET'], "mysharedsecret")
        self.fs.RemoveFile(config_file)

    def test_configure_grafana(self):
        config_file = "/etc/sysconfig/openattic"
        self.fs.CreateFile(config_file, contents="")
        openattic.configure_grafana("grafana.localhost")
        config = configobj.ConfigObj(config_file)
        self.assertEqual(config['GRAFANA_API_HOST'], "grafana.localhost")
        self.fs.RemoveFile(config_file)

    def test_no_config_file(self):
        config_file = "/etc/sysconfig/openattic"
        with self.assertRaises(CommandExecutionError) as ctx:
            openattic.configure_grafana("grafana.localhost")
        self.assertEqual(str(ctx.exception),
                         "No openATTIC config file found in the following locations: "
                         "('/etc/sysconfig/openattic', '/etc/openattic')")

    def test_salt_api_upgrade(self):
        config_file = "/etc/sysconfig/openattic"
        self.fs.CreateFile(config_file,
                           contents="SALT_API_HOST=mysalt.localhost\n"
                                    "SALT_API_PORT=8000\n"
                                    "SALT_API_EAUTH=auto\n"
                                    "SALT_API_USERNAME=myuser\n"
                                    "SALT_API_PASSWORD=mypassword\n")
        openattic.configure_salt_api("salt.localhost", 9000, "admin", "mysharedsecret")
        config = configobj.ConfigObj(config_file)
        self.assertEqual(config['SALT_API_HOST'], "mysalt.localhost")
        self.assertEqual(config['SALT_API_PORT'], "8000")
        self.assertEqual(config['SALT_API_USERNAME'], "admin")
        self.assertEqual(config['SALT_API_EAUTH'], "sharedsecret")
        self.assertEqual(config['SALT_API_SHARED_SECRET'], "mysharedsecret")
        self.fs.RemoveFile(config_file)
