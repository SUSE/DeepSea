import salt.client

import sys
sys.path.insert(0, 'srv/modules/runners')
sys.path.insert(0, 'srv/modules/runners/utils')

import yaml

from srv.modules.runners import upgrade

old_dg = """
drive_group_ssd-backed:
  target: 'I@roles:storage'
  data_devices:
    size: '39GB:41GB:'
  db_devices:
    size: ':21GB'
drive_group_nvme:
  target: 'I@roles:storage'
  data_devices:
    size: '23GB:26GB:'
"""

new_dg = """data_devices:
  size: '39GB:41GB:'
db_devices:
  size: :21GB
filter_logic: OR
placement:
  hosts:
  - host1
service_id: drive_group_ssd-backed
service_type: osd
---
data_devices:
  size: '23GB:26GB:'
filter_logic: OR
placement:
  hosts:
  - host1
service_id: drive_group_nvme
service_type: osd
"""

def test_upgrade_old_dgs():
    storage_hosts = [
        'host1'
    ]
    old = yaml.safe_load_all(old_dg)
    new = list(upgrade.upgrade_orig_drive_group(old, storage_hosts))
    new_txt = yaml.safe_dump_all(new)
    assert new_txt == new_dg
