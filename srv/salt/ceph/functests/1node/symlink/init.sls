
{% set node = salt.saltutil.runner('select.first', roles='storage') %}

Check split partition on symlinks:
  salt.state:
    - tgt: {{ node }}
    - tgt_type: compound
    - sls: ceph.tests.symlink

