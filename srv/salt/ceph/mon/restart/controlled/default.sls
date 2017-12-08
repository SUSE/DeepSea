{% if salt['cephprocesses.need_restart'](role='mon') == True %}

restart:
  cmd.run:
    - name: "systemctl restart ceph-mon@{{ grains['host'] }}.service"
    - unless: "systemctl is-failed ceph-mon@{{ grains['host'] }}.service"
    - fire_event: True

unset mon restart grain:
  module.run:
    - name: grains.setval
    - key: restart_mon
    - val: False

{% else %}

monrestart.noop:
  test.nop

{% endif %}
