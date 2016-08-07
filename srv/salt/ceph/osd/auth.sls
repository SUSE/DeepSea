

include:
  - .keyring

keyring_osd_auth_add:
  module.run:
    - name: ceph.keyring_osd_auth_add
    - require:
      - module: keyring_osd_save

