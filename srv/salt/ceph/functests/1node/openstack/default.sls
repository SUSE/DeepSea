{% set master = salt['master.minion']() %}

clean environment at start:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.tests.openstack.clean

apply ceph.openstack:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.openstack

verify users:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.tests.openstack.users

verify pools:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.tests.openstack.pools

clean environment at end:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.tests.openstack.clean

