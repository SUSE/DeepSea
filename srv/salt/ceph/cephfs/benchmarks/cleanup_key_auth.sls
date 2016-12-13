
remove key file:
  file.absent:
    - name: {{ salt['keyring.file']('deepsea_cephfs_bench') }}

remove secrets file:
  file.absent:
    - name: {{ salt['keyring.file']('deepsea_cephfs_bench_secret') }}

remove key auth:
  cmd.run:
    - name: 'ceph auth del client.deepsea_cephfs_bench'
