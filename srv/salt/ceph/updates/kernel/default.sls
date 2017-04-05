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
    - name: packagemanager.up
    - kwargs:
        'reboot': False
        'debug': False
        'kernel': True
    - fire_event: True

