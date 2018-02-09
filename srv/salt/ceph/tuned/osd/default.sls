/etc/tuned/ses-osd/tuned.conf:
  file.managed:
    - source: salt://ceph/tuned/ses-osd/tuned.conf
    - makedirs: True
    - user: root
    - group: root
    - mode: 644

start tuned:
  service.running:
    - name: tuned
    - enable: True

apply tuned ses osd:
  tuned.profile:
    - name: "ses-osd"
