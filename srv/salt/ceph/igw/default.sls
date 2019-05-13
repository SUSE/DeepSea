
install ceph-iscsi dependencies:
  pkg.installed:
    - pkgs:
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

clean lio configuration:
  deepsea.state_apply_if:
    - condition:
        grains:
          igw_clean_lio: True
    - state_name: cmd.run
    - kwargs:
        name: targetcli clearconfig confirm=true
        fire_event: True
    - fire_event: True

unset igw clean lio grain:
  module.run:
    - name: grains.setval
    - key: igw_clean_lio
    - val: False

install ceph-iscsi:
  pkg.installed:
    - pkgs:
      - ceph-iscsi
    - fire_event: True

enable rbd-target-api:
  service.running:
    - name: rbd-target-api
    - enable: True
    - fire_event: True
