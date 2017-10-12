

lrbd:
  pkg.installed:
    - pkgs:
      - lrbd
    - refresh: True

/tmp/lrbd.conf:
  file.managed:
    - source: 
      - salt://ceph/igw/cache/lrbd.conf
    - user: root
    - group: root
    - mode: 600

configure:
  cmd.run:
    - name: ". /etc/sysconfig/lrbd; lrbd -v $LRBD_OPTIONS -f /tmp/lrbd.conf"
    - shell: /bin/bash
    - require:
      - file: /tmp/lrbd.conf
    - unless: 'cat /tmp/lrbd.conf | grep -q "\"pools\": \[\]$"'
