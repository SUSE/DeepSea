
/etc/sysconfig/lrbd:
  file.managed:
    - source: 
      - salt://ceph/iscsi/files/sysconfig.lrbd
    - user: root
    - group: root
    - mode: 644

