zypper -n in -t pattern apparmor:
  cmd.run

/etc/apparmor.d/usr.bin.ceph-mds:
  file.managed:
    - source: salt://ceph/apparmor/files/usr.bin.ceph-mds
    - perms: 600
    - user: root
    - group: root

/etc/apparmor.d/usr.bin.ceph-mgr:
  file.managed:
    - source: salt://ceph/apparmor/files/usr.bin.ceph-mgr
    - perms: 600
    - user: root
    - group: root

/etc/apparmor.d/usr.bin.ceph-mon:
  file.managed:
    - source: salt://ceph/apparmor/files/usr.bin.ceph-mon
    - perms: 600
    - user: root
    - group: root

/etc/apparmor.d/usr.bin.ceph-osd:
  file.managed:
    - source: salt://ceph/apparmor/files/usr.bin.ceph-osd
    - perms: 600
    - user: root
    - group: root

/etc/apparmor.d/usr.bin.radosgw:
  file.managed:
    - source: salt://ceph/apparmor/files/usr.bin.radosgw
    - perms: 600
    - user: root
    - group: root

/etc/apparmor.d/ceph.d/common:
  file.managed:
    - source: salt://ceph/apparmor/files/ceph.d/common
    - makedirs: True
    - perms: 600
    - user: root
    - group: root

apparmor:
  service.running: []

aa-enforce /etc/apparmor.d/usr.bin.ceph-mds:
  cmd.run

aa-enforce /etc/apparmor.d/usr.bin.ceph-mgr:
  cmd.run

aa-enforce /etc/apparmor.d/usr.bin.ceph-mon:
  cmd.run

aa-enforce /etc/apparmor.d/usr.bin.ceph-osd:
  cmd.run

aa-enforce /etc/apparmor.d/usr.bin.radosgw:
  cmd.run
