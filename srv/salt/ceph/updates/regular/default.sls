zypper update regular:
  module.run:
    - name: update.zypper_up
    - kwargs:
        'debug': True
        'kernel': False
        'upgrade': False
    - fire_event: True
