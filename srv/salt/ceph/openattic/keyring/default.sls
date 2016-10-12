
/etc/ceph/ceph.client.openattic.keyring:
  file.managed:
    - source: 
      - salt://ceph/openattic/cache/ceph.client.openattic.keyring
    - user: openattic
    - group: openattic
    - mode: 660

