zypper dup:
  module.run:
    - name: update.zypper_up
    - kwargs:
        'debug': True
        'kernel': True
        'upgrade': True
    - fire_event: True
