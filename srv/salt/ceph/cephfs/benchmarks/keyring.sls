
cephfs bench keyring:
  file.managed:
    - name: /etc/ceph/ceph.client.deepsea_cephfs_bench.secret
    - source: salt://ceph/cephfs/benchmarks/files/cache/deepsea_cephfs_bench.secret
    - user: root
    - group: salt
    - mode: 640
    - makedirs: True
    - fire_event: True
