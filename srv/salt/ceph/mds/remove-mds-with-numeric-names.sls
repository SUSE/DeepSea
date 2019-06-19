mds nop:
  test.nop

{% set name = grains['host'] %}
{% if name != salt['mds.get_name'](name) %}
stop mds {{ name }}:
  service.dead:
    - name: ceph-mds@{{ name }}
    - enable: False

/var/lib/ceph/mds/ceph-{{ name }}/keyring:
  file.absent
{% endif %}

