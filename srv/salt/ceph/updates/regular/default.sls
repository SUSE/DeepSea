zypper update regular:
  module.run:
    - name: packagemanager.up
    - kwargs:
        'reboot': True
        'debug': False
        'kernel': False
    - fire_event: True
