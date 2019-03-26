
ceph-iscsi:
  pkg.installed:
    - pkgs:
      - ceph-iscsi
      - python3-targetcli-fb
      - tcmu-runner
      - tcmu-runner-handler-rbd
    - refresh: True
    - fire_event: True

enable tcmu-runner:
  service.running:
    - name: tcmu-runner
    - enable: True
    - fire_event: True

enable rbd-target-api:
  service.running:
    - name: rbd-target-api
    - enable: True
    - fire_event: True

