warning about ceph flag:
  module.run:
    - name: advise.generic 
    - message: "Make sure you have the 'noout' flag _UNSET_ after a successfull upgrade"
    - fire_event: True
    - failhard: True
