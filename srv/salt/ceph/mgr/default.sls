
include:
  - .keyring

start mgr:
  service.running:
    - name: ceph-mgr@{{ grains['host'] }}
    - enable: True


