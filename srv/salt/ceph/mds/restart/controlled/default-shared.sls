{% if salt['cephprocesses.need_restart'](role='mds') == True %}

restart:
  cmd.run:
    - name: "systemctl restart ceph-mds@{{ grains['host'] }}.service"
    - unless: "systemctl is-failed ceph-mds@{{ grains['host'] }}.service"
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
