
mds nop:
  test.nop

{% if 'mds' not in salt['pillar.get']('roles') %}
{% for i in range(salt['pillar.get']('mds_daemons_per_node', 1)) %}

{% set name = salt['mds.get_name'](grains['host'], i) %}
stop mds {{ name }}:
  service.dead:
    - name: ceph-mds@{{ name }}
    - enable: False

stop mds {{ name }} noid:
  service.dead:
    - name: ceph-mds@mds
    - enable: False

{% endfor %}

include:
- .keyring

{% else %}
{% set existing_mds = salt['mds.get_local_daemon_count']() %}
{% for i in range(salt['pillar.get']('mds_daemons_per_node', 1), existing_mds) %}

{% set name = salt['mds.get_name'](grains['host'], i) %}
stop mds {{ name }}:
  service.dead:
    - name: ceph-mds@{{ name }}
    - enable: False

stop mds {{ name }} noid:
  service.dead:
    - name: ceph-mds@mds
    - enable: False

/var/lib/ceph/mds/ceph-{{ name }}/keyring:
  file.absent
{% endfor %}

{% endif %}
