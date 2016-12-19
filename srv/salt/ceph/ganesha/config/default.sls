
/srv/salt/ceph/ganesha/cache/ganesha.conf:
  file.managed:
    - source:
      - salt://ceph/ganesha/files/ganesha.conf.j2
    - template: jinja
    - makedirs: True
    - user: root
    - group: root
    - mode: 644 

