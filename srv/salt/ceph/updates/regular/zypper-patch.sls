packagemanager update regular:
  module.run:
    - name: packagemanager.patch
    - kwargs:
        'reboot': {{ salt['pillar.get']('auto_reboot', True) }} 
        'debug': {{ salt['pillar.get']('debug', False) }} 
        'kernel': False
    - fire_event: True
