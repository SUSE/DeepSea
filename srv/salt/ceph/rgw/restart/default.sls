restart:
  cmd.run:
    - name: "systemctl restart ceph-radosgw@rgw.{{ host }}.service"
    - fire_event: True
