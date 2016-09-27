

/var/lib/ceph/mds/ceph-mds/keyring:
  file.managed:
    - source:
      - salt://ceph/mds/cache/mds.keyring
    - template: jinja
    - user: ceph
    - group: ceph
    - mode: 600
    - makedirs: True
    - fire_event: True

