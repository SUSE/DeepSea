
install rgw:
  pkg.installed:
    - pkgs:
      - ceph-radosgw
      - python-boto

add users:
  module.run:
    - name: rgw.add_users
