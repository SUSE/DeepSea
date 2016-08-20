
/etc/multipath.conf:
  file.managed:
    - source: 
      - salt://ceph/files/multipath.conf
    - user: root
    - group: root
    - mode: 600

multipathd:
  service.running:
    - name: multipathd
    - enable: True

