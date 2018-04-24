
include:
  - .install
  - .profiles

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

aa-enforce /etc/apparmor.d/usr.sbin.httpd-prefork:
  cmd.run

aa-enforce /etc/apparmor.d/usr.sbin.oaconfig:
  cmd.run
