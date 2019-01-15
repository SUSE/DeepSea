packagemanager dup:
  module.run:
    - name: packagemanager.dup
    - kwargs:
        'debug': False
        'reboot': False
        'kernel': True
    - fire_event: True
      # testing, revert later FIXME
    - failhard: False
