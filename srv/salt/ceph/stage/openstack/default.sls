
{% set master = salt['master.minion']() %}

openstack:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.openstack

