restart:
  cmd.run:
    - name: "systemctl restart ceph-mgr@{{ grains['host'] }}.service"
    - unless: "systemctl is-failed ceph-mgr@{{ grains['host'] }}.service"
    - fire_event: True
