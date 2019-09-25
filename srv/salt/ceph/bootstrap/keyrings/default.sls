
keyrings:
  file.managed:
    - names:
      - '/var/lib/ceph/tmp/keyring':
        - source: 'salt://ceph/bootstrap/files/keyring'
      - '/var/lib/ceph/tmp/ceph.keyring':
        - source: 'salt://ceph/bootstrap/files/ceph.keyring'

