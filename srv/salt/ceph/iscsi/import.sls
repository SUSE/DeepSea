
lrbd install:
  pkg.installed:
    - name: lrbd

/tmp/lrbd.conf:
  file.managed:
    - source: 
      - salt://ceph/iscsi/files/lrbd.conf
    - user: root
    - group: root
    - mode: 600

configure:
  cmd.run:
    - name: "lrbd -f /tmp/lrbd.conf"
    - shell: /bin/bash
    - require:
      - file: /tmp/lrbd.conf

