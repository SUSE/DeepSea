
{% if grains['id'] not in salt['pillar.get']('time_server') %}
/etc/ntp.conf:
  file.absent

stop ntpd:
  service.dead:
    - name: ntpd
    - enable: False
    - fire_event: True

uninstall ntp:
  pkg.removed:
    - name: ntp
{% endif %}

prevent empty ntp:
  test.nop

