
{% if grains['id'] not in salt['pillar.get']('time_server') %}

/etc/chrony.conf:
  file.absent

stop chronyd:
  service.dead:
    - name: chronyd
    - enable: False
    - fire_event: True

uninstall chronyd:
  pkg.removed:
    - name: chronyd

{% endif %}

prevent empty chrony:
  test.nop
