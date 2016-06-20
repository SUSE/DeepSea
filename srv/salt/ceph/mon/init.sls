# We need to install ceph and its configuration library


/etc/ceph/ceph.conf:
  file:
    - managed
    - source:
        # Where to get the source file will have to be customized to your environment.
        - salt://ceph/files/ceph.conf.j2
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - makedirs: True


#
keyring_admin_save:
  module.run:
    - name: ceph.keyring_save
    - kwargs: {
        'keyring_type' : 'admin',
        'secret' : {{ salt['pillar.get']('keyring:admin') }} 
        }
    - require:
      - file: /etc/ceph/ceph.conf


keyring_mon_save:
  module.run:
    - name: ceph.keyring_save
    - kwargs: {
        'keyring_type' : 'mon',
        'secret' : {{ salt['pillar.get']('keyring:mon') }}
        }
    - require:
      - file: /etc/ceph/ceph.conf


mon_create:
  module.run:
    - name: ceph.mon_create
    - require:
      - module: keyring_admin_save
      - module: keyring_mon_save

