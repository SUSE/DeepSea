

keyring_admin_save:
  module.run:
    - name: ceph.keyring_save
    - kwargs: {
        'keyring_type' : 'admin',
        'secret' : {{ salt['pillar.get']('keyring:admin') }} 
        }


