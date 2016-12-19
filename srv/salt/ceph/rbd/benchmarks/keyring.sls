
rbd bench keyring:
  file.managed:
    - name: /etc/ceph/ceph.client.deepsea_rbd_bench.keyring
    - source: salt://ceph/rbd/benchmarks/files/cache/deepsea_rbd_bench.keyring
    - user: root
    - group: salt
    - mode: 640
    - makedirs: True
    - fire_event: True
