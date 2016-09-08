

keyring_mds_save:
  module.run:
    - name: ceph.keyring_save
    - kwargs: {
        'keyring_type' : 'mds',
        'secret' : {{ salt['pillar.get']('keyring:mds') }}
        }
    - fire_event: True

keyring_auth_add_mds:
  module.run:
    - name: ceph.keyring_mds_auth_add
    - require:
      - module: keyring_mds_save
    - fire_event: True

mds_create:
  module.run:
    - name: ceph.mds_create
    - kwargs: {
        name: mds.{{ grains['host'] }},
        port: 6800,
        addr: {{ salt['pillar.get']('public_address') }}
      }
    - fire_event: True
