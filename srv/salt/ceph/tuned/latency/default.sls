
/etc/tuned/ceph-latency/tuned.conf:
  file.managed:
    - source: salt://ceph/tuned/files/latency.conf
    - makedirs: True
    - user: root
    - group: root
    - mode: 644

start tuned for latency profile:
  service.running:
    - name: tuned
    - enable: True

apply latency profile:
  cmd.run:
    - name: 'tuned-adm profile ceph-latency'

