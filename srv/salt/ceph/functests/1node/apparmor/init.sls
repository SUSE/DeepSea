{% set master = salt['master.minion']() %}

enforce apparmor profiles:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - tgt_type: compound
    - sls: ceph.apparmor.default-enforce
    - failhard: True

# The below test is insufficient; as of 2019-03-27,
# the apparmor profile for ceph-mgr won't let ceph-mgr
# operate correctly, but you only notice this if ceph-mgr
# is restarted.  If it's already running the cluster will
# remain healthy.
# TODO: restart all daemons after putting apparmor into
# enforcing mode, *then* check the cluster health
make sure ceph cluster is healthy:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.wait
    - failhard: True

disable apparmor profiles:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - tgt_type: compound
    - sls: ceph.apparmor.default-disable
    - failhard: True
