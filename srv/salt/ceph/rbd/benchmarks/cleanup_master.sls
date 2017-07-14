delete benchmark image:
  cmd.run:
    - name: rbd rm deepsea_benchmark

remove key file:
  file.absent:
    - name: {{ salt['keyring.file']('deepsea_rbd_bench') }}

remove key auth:
  cmd.run:
    - name: 'ceph auth del client.deepsea_rbd_bench'
