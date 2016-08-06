
/etc/ceph/ceph.client.openattic.keyring:
  file.managed:
    - source: 
      - salt://ceph/openattic/files/ceph.client.openattic.keyring
    - user: openattic
    - group: openattic
    - mode: 600

