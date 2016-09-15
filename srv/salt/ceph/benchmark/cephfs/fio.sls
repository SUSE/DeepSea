
fio:
  pkg.installed:
    - pkgs:
        - fio

/etc/systemd/system/fio.service:
  file.managed:
    - source:
      - salt://ceph/benchmark/cephfs/files/fio.service
      - user: root
      - group: root
      - file_mode: 664

fio:
  service.running: []
