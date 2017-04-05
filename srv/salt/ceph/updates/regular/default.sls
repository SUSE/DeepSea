packagemanager update regular:
  module.run:
    - name: packagemanager.up
    - kwargs:
        'reboot': False
        'debug': False
        'kernel': False
    - fire_event: True
