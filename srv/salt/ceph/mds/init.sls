

keyring_mds_save:
  module.run:
    - name: ceph.keyring_save
    - kwargs: {
        'keyring_type' : 'mds',
        'secret' : {{ salt['pillar.get']('keyring:mds') }}
        }

keyring_auth_add_mds:
  module.run:
    - name: ceph.keyring_mds_auth_add
    - require:
      - module: keyring_mds_save

mds_create:
  module.run:
    - name: ceph.mds_create
    - kwargs: {
        name: mds.{{ grains['host'] }},
        port: 6800,
        addr: {{ salt['pillar.get']('public_address') }}
      }
