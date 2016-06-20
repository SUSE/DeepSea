
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

keyring_osd_save:
  module.run:
    - name: ceph.keyring_save
    - kwargs: {
        'keyring_type' : 'osd',
        'secret' : {{ salt['pillar.get']('keyring:osd') }}
        }
    - require:
      - file: /etc/ceph/ceph.conf


keyring_osd_auth_add:
  module.run:
    - name: ceph.keyring_osd_auth_add
    - require:
      - module: keyring_admin_save
      - module: keyring_osd_save

include:
  - .{{ salt['pillar.get']('osd_method') }}

