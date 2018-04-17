
{% set master = salt['master.minion']() %}

setting noout:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.noout.set
    - failhard: True
