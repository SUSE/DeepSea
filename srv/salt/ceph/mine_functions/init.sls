

configure_mine_functions:
  file.managed:
    - name: /etc/salt/minion.d/mine_functions.conf
    - source: salt://ceph/mine_functions/files/mine_functions.conf

manage_salt_minion_for_mine_functions:
  service.running:
    - name: salt-minion
    - watch:
      - file: configure_mine_functions

