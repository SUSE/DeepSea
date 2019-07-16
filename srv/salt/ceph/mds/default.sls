
include:
  - .keyring

{% set name = salt['mds.get_name'](grains['host']) %}
start mds:
  service.running:
    - name: ceph-mds@{{ name }}
    - enable: True
 

