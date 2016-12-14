
/etc/ganesha/ganesha.conf:
  file.managed:
    - source:
      - salt://ceph/ganesha/files/ganesha.conf.j2
    - template: jinja
    - user: root
    - group: root
    - mode: 644 

