
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

/etc/apparmor.d/usr.sbin.httpd-prefork:
  file.managed:
    - source: salt://ceph/apparmor/files/usr.sbin.httpd-prefork
    - perms: 600
    - user: root
    - group: root

/etc/apparmor.d/usr.sbin.oaconfig:
  file.managed:
    - source: salt://ceph/apparmor/files/usr.sbin.oaconfig
    - perms: 600
    - user: root
    - group: root
