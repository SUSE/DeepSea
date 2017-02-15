zypper dup:
  module.run:
    - name: zypper.dup
    - kwargs:
        'debug': True
        'kernel': True
    - fire_event: True
