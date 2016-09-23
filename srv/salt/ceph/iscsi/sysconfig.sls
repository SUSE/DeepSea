
/etc/sysconfig/lrbd:
  file.managed:
    - source: 
      - salt://ceph/iscsi/files/sysconfig.lrbd.j2
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - context:
      client: "client.igw.{{ grains['host'] }}"

