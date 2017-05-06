
restart apache2:
  module.run:
    - name: service.restart
    - m_name: apache2

oaconfig:
  cmd.run:
    - name: "oaconfig install --allow-broken-hostname"

restart icinga:
  module.run:
    - name: service.restart
    - m_name: icinga
