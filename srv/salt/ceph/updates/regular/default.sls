zypper update regular:
  module.run:
    - name: packagemanager.up
    - kwargs:
        'reboot': True
        'debug': True
        'kernel': False
    - fire_event: True
