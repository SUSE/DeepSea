restart igw gateway (lrbd):
  deepsea.state_apply_if:
    - condition:
        salt:
          cephprocesses.need_restart:
            kwargs:
              role: igw
        pillar_notexists:
          - igw_service_daemons
    - state_name: module.run
    - kwargs:
        name: service.restart
        m_name: lrbd

restart igw gateway (ceph-iscsi):
  deepsea.state_apply_if:
    - condition:
        salt:
          cephprocesses.need_restart:
            kwargs:
              role: igw
        pillar:
          igw_service_daemons: [rbd-target-api]
    - state_name: module.run
    - kwargs:
        name: service.restart
        m_name: rbd-target-api

wait for iscsi gateway to initialize:
  deepsea.state_apply_if:
    - condition:
        pillar:
          igw_service_daemons: [rbd-target-api]
    - state_name: module.run
    - kwargs:
        name: iscsi.wait_for_gateway

unset igw restart grain:
  module.run:
    - name: grains.setval
    - key: restart_igw
    - val: False
