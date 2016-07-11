

/etc/ceph/ceph.conf:
  file:
    - managed
    - source:
        - salt://ceph/files/ceph.conf.j2
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - makedirs: True



keyring_admin_save:
  module.run:
    - name: ceph.keyring_save
    - kwargs: {
        'keyring_type' : 'admin',
        'secret' : {{ salt['pillar.get']('keyring:admin') }} 
        }
    - require:
      - file: /etc/ceph/ceph.conf


