

keyring_rgw_save:
  module.run:
    - name: ceph.keyring_save
    - kwargs: {
        'keyring_type' : 'rgw',
        'secret' : {{ salt['pillar.get']('keyring:rgw') }}
        }

keyring_auth_add_rgw:
  module.run:
    - name: ceph.keyring_rgw_auth_add
    - require:
      - module: keyring_rgw_save

rgw_create:
  module.run:
    - name: ceph.rgw_create
    - kwargs: {
        name: mds.{{ grains['host'] }},
      }
    - require:
      - module: rgw_prep

