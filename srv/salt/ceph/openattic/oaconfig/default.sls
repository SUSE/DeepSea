
restart apache2:
  cmd.run:
    - name: "systemctl restart apache2"

oaconfig:
  cmd.run:
    - name: "oaconfig install --allow-broken-hostname"

restart icinga:
  cmd.run:
    - name: "systemctl restart icinga"
