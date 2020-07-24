
/etc/ceph/ceph.client.crash.keyring:
  file.managed:
    - source:
      - salt://ceph/crash/cache/ceph.client.crash.keyring
    - user: root
    - group: root
    - mode: 600

