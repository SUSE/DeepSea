
ceph-iscsi:
  pkg.installed:
    - pkgs:
      - ceph-iscsi
      - targetcli-fb
      - tcmu-runner
      - tcmu-runner-handler-rbd
    - refresh: True
    - fire_event: True

enable tcmu-runner:
  service.running:
    - name: tcmu-runner
    - enable: True
    - fire_event: True

enable rbd-target-gw:
  service.running:
    - name: rbd-target-gw
    - enable: True
    - fire_event: True

