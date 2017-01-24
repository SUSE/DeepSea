/etc/ganesha/ganesha.conf:
  file.managed:
    - source:
      - salt://ceph/ganesha/cache/ganesha.conf
    - template: jinja
    - user: root
    - group: root
    - mode: 644

