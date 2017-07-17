packagemanager migrate:
  module.run:
    - name: packagemanager.migrate
    - kwargs:
        'reboot': {{ salt['pillar.get']('auto_reboot', True) }} 
    - fire_event: True
    - failhard: True
