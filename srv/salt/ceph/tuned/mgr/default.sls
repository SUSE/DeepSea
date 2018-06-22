/etc/tuned/ses-mgr/tuned.conf:
  file.managed:
    - source: salt://ceph/tuned/files/ses-mgr/tuned.conf
    - makedirs: True
    - user: root
    - group: root
    - mode: 644

start tuned:
  service.running:
    - name: tuned
    - enable: True

apply tuned ses mgr:
  cmd.run:
    - name: 'tuned-adm profile ses-mgr'
