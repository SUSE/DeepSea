

keyring_mon_save:
  module.run:
    - name: ceph.keyring_save
    - kwargs: {
        'keyring_type' : 'mon',
        'secret' : {{ salt['pillar.get']('keyring:mon') }}
        }
    - fire_event: True


mon_create:
  module.run:
    - name: ceph.mon_create
    - fire_event: True


