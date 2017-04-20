update salt:
  pkg.latest:
    - pkgs:
      - salt-minion 
    - dist-upgrade: True

restart salt-minion:
  module.run:
    - name: service.restart
    - m_name: salt-minion

