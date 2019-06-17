{% if salt['cephprocesses.need_restart'](role='mds') == True %}
{% set name = salt['mds.get_name'](grains['host']) %}

restart:
  cmd.run:
    - name: "systemctl restart ceph-mds@{{ name }}.service"
    - unless: "systemctl is-failed ceph-mds@{{ name }}.service"
    - fire_event: True

unset mds restart grain:
  module.run:
    - name: grains.setval
    - key: restart_mds
    - val: False


{% else %}

mdsrestart.noop:
  test.nop

{% endif %}
