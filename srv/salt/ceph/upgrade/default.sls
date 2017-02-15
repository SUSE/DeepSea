zypper dup:
  module.run:
    - name: packagemanager.dup
    - kwargs:
        'debug': True
        'kernel': True
    - fire_event: True
