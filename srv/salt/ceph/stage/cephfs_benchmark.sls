
fio:
  salt.state:
    - tgt: "I@roles:cephs-client and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.benchmark.cephfs.fio
      - ceph.benchmark.cephfs.mount

{% for run in salt['pillar.get']('runs') %}
{{ run['operation'] }}:
  file.managed:
    - template: jinja
    - source: salt://ceph/benchmark/cephfs/files/fio_jobs/job.fio.j2
    - name: /var/run/cephfs_bench/{{ run['operation'] }}
    - context:
      blocksize: {{ run['blocksize'] }}
      dir: {{ run['dir'] }}
      filesize: {{ run['filesize'] }}
      number_of_workers: {{ run['number_of_workers'] }}
      operation: {{ run['operation'] }}

run {{ run['operation'] }}:
  salt.runner:
    - name: benchmark.run
    - job: /var/run/cephfs_bench/{{ run['operation'] }}
{% endfor %}
