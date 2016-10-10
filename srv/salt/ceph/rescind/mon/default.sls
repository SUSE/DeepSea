
mon nop:
  test.nop

{% if 'mon' not in salt['pillar.get']('roles') %}
stop mon:
  service.dead:
    - name: ceph-mon@{{ grains['host'] }}
    - enable: False

/var/lib/ceph/mon/{{ salt['pillar.get']('cluster') }}-{{ grains['host'] }}:
  file.absent

/var/lib/ceph/tmp/keyring.mon:
  file.absent
{% endif %}


