switch kernel:
  module.run:
    - name: kernel.replace
    - kwargs:
        os:
          SUSE:
            kernel: kernel-default
            candidates:
            - kernel-default-base

packagemanager patch only kernel:
  module.run:
    - name: packagemanager.up
    - kwargs:
        'reboot': {{ salt['pillar.get']('auto_reboot', True) }}
        'debug': {{ salt['pillar.get']('debug', False) }}
        'kernel': True
    - fire_event: True
