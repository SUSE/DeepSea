

keyring_osd_save:
  module.run:
    - name: ceph.keyring_save
    - kwargs: {
        'keyring_type' : 'osd',
        'secret' : {{ salt['pillar.get']('keyring:osd') }}
        }


