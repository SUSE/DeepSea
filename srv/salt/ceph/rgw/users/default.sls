
install rgw:
  pkg.installed:
    - name: ceph-radosgw

add users:
  module.run:
    - name: rgw.add_users
