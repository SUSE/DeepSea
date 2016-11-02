switch kernel:
  module.run:
    - name: kernel.replace
    - kwargs:
        os: 
          SUSE: 
            kernel: kernel-default
            candidates:
            - kernel-default-base

zypper update only kernel:
  module.run:
    - name: update.zypper_up
    - kwargs:
        'debug': True
        'kernel': True
        'upgrade': False
    - fire_event: True

