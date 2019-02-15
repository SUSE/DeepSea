
save gateway.conf:
  cmd.run:
    - name: "rados -p rbd get gateway.conf /srv/salt/ceph/igw/cache/gateway.conf"

remove gateway.conf:
  cmd.run:
    - name: "rados -p rbd rm gateway.conf"
