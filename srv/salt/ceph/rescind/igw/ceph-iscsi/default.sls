
stop rbd-target-gw:
  service.dead:
    - name: rbd-target-gw
    - enable: False

stop rbd-target-api:
  service.dead:
    - name: rbd-target-api
    - enable: False

uninstall ceph-iscsi:
  pkg.removed:
    - name: ceph-iscsi

/etc/ceph/iscsi-gateway.cfg:
  file.absent

