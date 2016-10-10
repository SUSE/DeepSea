
mds nop:
  test.nop

{% if 'mds' not in salt['pillar.get']('roles') %}
stop mds {{ grains['host'] }}:
  service.dead:
    - name: ceph-mds@{{ grains['host'] }}
    - enable: False

stop mds:
  service.dead:
    - name: ceph-mds@mds
    - enable: False

include:
- .keyring
{% endif %}
