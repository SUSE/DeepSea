

keyring_osd_save:
  module.run:
    - name: ceph.keyring_save
    - kwargs: {
        'keyring_type' : 'osd',
        'secret' : {{ salt['pillar.get']('keyring:osd') }}
        }


keyring_osd_auth_add:
  module.run:
    - name: ceph.keyring_osd_auth_add
    - require:
      - module: keyring_osd_save

include:
  - .{{ salt['pillar.get']('osd_creation') }}

