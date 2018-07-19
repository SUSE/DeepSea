/etc/tuned/ceph-mgr/tuned.conf:
  file.managed:
    - source: salt://ceph/tuned/files/ceph-mgr/tuned.conf
    - makedirs: True
    - user: root
    - group: root
    - mode: 644

start tuned:
  service.running:
    - name: tuned
    - enable: True

apply tuned ceph mgr:
  cmd.run:
    - name: 'tuned-adm profile ceph-mgr'
