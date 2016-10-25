restart:
  cmd.run:
    - name: "systemctl restart ceph-mds@{{ grains['host'] }}.service"
    - fire_event: True

