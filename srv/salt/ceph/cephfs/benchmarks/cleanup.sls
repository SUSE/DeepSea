
include:
  - ceph.tools.fio.cleanup

unmount cephfs:
  mount.unmounted:
    - name: {{ salt['pillar.get']('benchmark:work-directory')}}

remove keyring:
  file.absent:
   - name: /etc/ceph/ceph.client.deepsea_cephfs_benchmark.secret
