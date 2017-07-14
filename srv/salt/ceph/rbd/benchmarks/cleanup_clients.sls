include:
  - ceph.tools.fio.cleanup

remove keyring:
  file.absent:
   - name: /etc/ceph/ceph.client.deepsea_rbd_benchmark.keyring
