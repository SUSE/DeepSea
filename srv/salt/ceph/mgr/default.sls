
include:
  - .keyring
  - .dashboard

start mgr:
  service.running:
    - name: ceph-mgr@{{ grains['host'] }}
    - enable: True

wait for mgr:
  module.run:
    - name: cephprocesses.wait
    - kwargs:
        'timeout': 6
        'delay': 2
        'roles':
          - mgr
    - fire_event: True
    - failhard: True
