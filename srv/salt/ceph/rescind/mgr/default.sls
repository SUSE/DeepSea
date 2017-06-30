
mgr nop:
  test.nop

{% if 'mgr' not in salt['pillar.get']('roles') %}
stop mgr {{ grains['host'] }}:
  service.dead:
    - name: ceph-mgr@{{ grains['host'] }}
    - enable: False

include:
- .keyring
{% endif %}
