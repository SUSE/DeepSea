
include:
  - .keyring

create parts:
  module.run:
    - name: disk_part.create


deploy OSDs:
  module.run:
    - name: osd.deploy_lvm

