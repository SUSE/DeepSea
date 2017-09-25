
/etc/sysctl.d/deepsea-aio-max-nr.conf:
  file.managed:
    - source: salt://ceph/sysctl/files/90-deepsea-aio-max-nr.conf
    - user: root
    - group: root
    - mode: 600


load sysctl:
  cmd.run:
    - name: "sysctl --system"


