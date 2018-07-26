{% set master = salt['pillar.get']('master_minion') %}

clean environment at start (prefix=smoketest):
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.tests.openstack.clean
    - pillar:
        "openstack_prefix": "smoketest"

apply ceph.openstack (prefix=smoketest):
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.openstack
    - pillar:
        "openstack_prefix": "smoketest"

verify users (prefix=smoketest):
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.tests.openstack.users
    - pillar:
        "openstack_prefix": "smoketest"

verify pools (prefix=smoketest):
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.tests.openstack.pools
    - pillar:
        "openstack_prefix": "smoketest"

clean environment at end (prefix=smoketest):
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.tests.openstack.clean
    - pillar:
        "openstack_prefix": "smoketest"

