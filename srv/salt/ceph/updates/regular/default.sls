zypper update regular:
  module.run:
    - name: zypper.up
    - kwargs:
        'debug': True
        'kernel': False
    - fire_event: True
