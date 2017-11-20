restart oA-systemd:
  cmd.run:
    - name: "systemctl restart openattic-systemd.service"
    - unless: "systemctl is-failed openattic-systemd.service"
    - fire_event: True

restart apache:
  cmd.run:
    - name: "systemctl restart apache2.service"
    - unless: "systemctl is-failed apache2.service"
    - fire_event: True
