
include:
  - .keyring

{% for i in range(salt['pillar.get']('mds_daemons_per_node', 1)) %}

{% set name = salt['mds.get_name'](grains['host'], i) %}

start mds {{ name }}:
  service.running:
    - name: ceph-mds@{{ name }}
    - enable: True

{% endfor %}

