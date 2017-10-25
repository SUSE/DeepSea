{% set pg_num = salt['calculate.pg_num']() %}

create benchmark pool:
  cmd.run:
    - name: ceph osd pool create {{ salt['pillar.get']('rbd_benchmark_pool', 'deepsea_rbd_benchmark') }} {{ pg_num }} {{ pg_num }}

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='storage') %}
create {{ host }} benchmark image:
  cmd.run:
    - name: rbd create --pool {{ salt['pillar.get']('rbd_benchmark_pool', 'deepsea_rbd_benchmark') }} --size 2048 {{ salt['pillar.get']('rbd_benchmark_image_prefix', 'rbd_bench_img_') }}{{ host }}
    - require:
      - create benchmark pool
{% endfor %}
