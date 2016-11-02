
include:
  - .keyring

start mds:
  service.running:
    - name: ceph-mds@mds
    - enable: True
 

