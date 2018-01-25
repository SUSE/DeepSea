
install rgw:
  pkg.installed:
    - pkgs:
      - ceph-radosgw
      - python3-boto
    - refresh: True

add users:
  module.run:
    - name: rgw.add_users
