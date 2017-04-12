switch kernel:
  module.run:
    - name: kernel.replace
    - kwargs:
        os: 
          SUSE: 
            kernel: kernel-default
            candidates:
            - kernel-default-base

packagemanager update only kernel:
  module.run:
    - name: packagemanager.patch
    - kwargs:
        'reboot': {{ salt['pillar.get']('auto_reboot', True) }} 
        'debug': {{ salt['pillar.get']('debug', False) }} 
        'kernel': True
    - fire_event: True

