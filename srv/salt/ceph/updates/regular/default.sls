zypper update regular:
  module.run:
    - name: packagemanager.up
    - kwargs:
        'debug': True
        'kernel': False
    - fire_event: True
