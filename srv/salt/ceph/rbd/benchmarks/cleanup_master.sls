delete benchmark pool:
  cmd.run:
    - name: ceph osd pool rm {{ salt['pillar.get']('rbd_benchmark_pool', 'deepsea_rbd_benchmark') }} {{ salt['pillar.get']('rbd_benchmark_pool', 'deepsea_rbd_benchmark') }} --yes-i-really-really-mean-it

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='storage') %}
delete {{ host }} benchmark image:
  cmd.run:
    - name: rbd rm --pool {{ salt['pillar.get']('rbd_benchmark_pool', 'deepsea_rbd_benchmark') }} {{ salt['pillar.get']('rbd_benchmark_image_prefix', 'rbd_bench_img_') }}{{ host }}
{% endfor %}

remove key file:
  file.absent:
    - name: {{ salt['keyring.file']('deepsea_rbd_bench') }}

remove key auth:
  cmd.run:
    - name: 'ceph auth del client.deepsea_rbd_bench'
