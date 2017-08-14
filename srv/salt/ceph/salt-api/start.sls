

enable salt-api:
  service.enabled:
    - name: salt-api

restart salt-api:
  module.run:
    - name: service.restart
    - m_name: salt-api

