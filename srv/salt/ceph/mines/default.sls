

configure_mines:
  file.managed:
    - name: /etc/salt/minion.d/mine_functions.conf
    - source: salt://ceph/mines/files/mine_functions.conf
    - fire_event: True

manage_salt_minion_for_mines:
  service.running:
    - name: salt-minion
    - watch:
      - file: configure_mines
    - fire_event: True

