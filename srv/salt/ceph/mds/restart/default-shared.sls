restart:
  cmd.run:
    - name: "systemctl restart ceph-mds@mds.service"
    - unless: "systemctl is-failed ceph-mds@mds.service"
    - fire_event: True
