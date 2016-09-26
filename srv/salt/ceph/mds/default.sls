
include:
  - .keyring

start mds:
  service.running:
    - name: ceph-mds@{{ grains['host'] }}
    - enable: True
 

