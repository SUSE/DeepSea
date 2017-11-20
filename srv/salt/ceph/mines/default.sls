

configure_mine_functions_conf:
  file.managed:
    - name: /etc/salt/minion.d/mine_functions.conf
    - source: salt://ceph/mines/files/mine_functions.conf
    - fire_event: True

add_mine_cephdisks.list_to_minion:
  module.run:
    - name: mine.send
    - func: cephdisks.list

manage_salt_minion_for_mines:
  module.run:
    - name: mine.update
    - watch:
      - file: configure_mine_functions_conf
    - fire_event: True

