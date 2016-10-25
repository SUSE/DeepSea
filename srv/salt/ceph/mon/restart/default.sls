restart:
  cmd.run:
    - name: "systemctl restart ceph-mon@{{ grains['host'] }}.service"
    - fire_event: True

