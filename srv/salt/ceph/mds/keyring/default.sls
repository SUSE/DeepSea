

{% set name = salt['mds.get_name'](grains['host']) %}
/var/lib/ceph/mds/ceph-{{ name }}/keyring:
  file.managed:
    - source:
      - salt://ceph/mds/cache/{{ name }}.keyring
    - template: jinja
    - user: ceph
    - group: ceph
    - mode: 600
    - makedirs: True
    - fire_event: True

