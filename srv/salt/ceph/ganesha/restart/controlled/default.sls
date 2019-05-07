restart nfs-ganesha:
  deepsea.state_apply_if:
    - condition:
        salt:
          cephprocesses.need_restart:
            kwargs:
              role: ganesha
    - state_name: module.run
    - kwargs:
        name: service.restart
        m_name: nfs-ganesha

unset ganesha restart grain:
  module.run:
    - name: grains.setval
    - key: restart_ganesha
    - val: False
