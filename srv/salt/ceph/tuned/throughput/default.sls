
/etc/tuned/ceph-throughput/tuned.conf:
  file.managed:
    - source: salt://ceph/tuned/files/throughput.conf
    - makedirs: True
    - user: root
    - group: root
    - mode: 644

start tuned for throughput profile:
  service.running:
    - name: tuned
    - enable: True

apply throughput profile:
  cmd.run:
    - name: 'tuned-adm profile ceph-throughput'

