restart:
  cmd.run:
    - name: "systemctl restart ceph-radosgw@rgw.{{ grains['host'] }}.service"
    - fire_event: True
