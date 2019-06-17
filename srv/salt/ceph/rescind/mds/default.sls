
mds nop:
  test.nop

{% if 'mds' not in salt['pillar.get']('roles') %}
{% set name = salt['mds.get_name'](grains['host']) %}
stop mds {{ name }}:
  service.dead:
    - name: ceph-mds@{{ name }}
    - enable: False

stop mds:
  service.dead:
    - name: ceph-mds@mds
    - enable: False

include:
- .keyring
{% endif %}
