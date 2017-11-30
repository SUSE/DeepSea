{% if salt['cephprocesses.need_restart'](role='mgr') == True %}

restart:
  cmd.run:
    - name: "systemctl restart ceph-mgr@{{ grains['host'] }}.service"
    - unless: "systemctl is-failed ceph-mgr@{{ grains['host'] }}.service"
    - fire_event: True

unset mgr restart grain:
  module.run:
    - name: grains.setval
    - key: restart_mgr
    - val: False

{% else %}

mgrrestart.noop:
  test.nop

{% endif %}
