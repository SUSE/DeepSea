
unmount cephfs:
  mount.unmounted:
    - name: {{ salt['pillar.get']('benchmark:work-directory')}}

remove keyring:
  file.absent:
   - name: /etc/ceph/ceph.client.deepsea_cephfs_benchmark.secret

stop fio:
  service.dead:
    - name: fio

remove fio service file:
  file.absent:
    - name: /etc/systemd/system/fio.service
