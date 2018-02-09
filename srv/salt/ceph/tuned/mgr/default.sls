/etc/tuned/ses-mgr/tuned.conf:
  file.managed:
    - source: salt://ceph/tuned/ses-mgr/tuned.conf
    - makedirs: True
    - user: root
    - group: root
    - mode: 644

start tuned:
  service.running:
    - name: tuned
    - enable: True

apply tuned ses mgr:
  tuned.profile:
    - name: "ses-mgr"
