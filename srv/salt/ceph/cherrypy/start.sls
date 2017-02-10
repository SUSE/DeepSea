

enable salt-api:
  service.running:
    - name: salt-api
    - enable: True

restart salt-master:
  module.run:
    - name: service.restart
    - m_name: salt-master

restart salt-api:
  module.run:
    - name: service.restart
    - m_name: salt-api

