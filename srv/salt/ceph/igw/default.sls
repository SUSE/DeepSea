
ceph-iscsi:
  pkg.installed:
    - pkgs:
      - ceph-iscsi
    - refresh: True

enable rbd-target-gw:
  service.running:
    - name: rbd-target-gw
    - enable: True

