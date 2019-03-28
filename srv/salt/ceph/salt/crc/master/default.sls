/etc/salt/master.d/crc_method.conf:
  file.managed:
    - source:
      - salt://ceph/salt/crc/crc_method.conf
