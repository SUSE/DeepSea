/etc/tuned/ses-mon/tuned.conf:
  file.managed:
    - source: salt://ceph/tuned/ses-mon/tuned.conf
    - makedirs: True
    - user: root
    - group: root
    - mode: 644

start tuned:
  service.running:
    - name: tuned
    - enable: True

apply tuned ses mon:
  tuned.profile:
    - name: "ses-mon"
