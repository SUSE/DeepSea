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
    - name: zypper.up
    - kwargs:
        'debug': True
        'kernel': True
    - fire_event: True

