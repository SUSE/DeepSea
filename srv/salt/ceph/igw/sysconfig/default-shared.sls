
/etc/sysconfig/lrbd:
  file.managed:
    - source:
      - salt://ceph/igw/files/sysconfig.lrbd.j2
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - context:
      client: "client.igw"

