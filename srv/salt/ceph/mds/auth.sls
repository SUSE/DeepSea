

{% for mds in salt.saltutil.runner('select.minions', host=True, cluster='ceph', roles='mds') %}

keyring {{ mds }}:
  file.managed:
    - name: /var/lib/ceph/mds/ceph-{{ grains['host'] }}/keyring
    - source:
      - salt://ceph/mds/files/keyring.j2
    - template: jinja
    - user: salt
    - group: salt
    - mode: 600
    - makedirs: True
    - context:
      mds: {{ mds }}
    - fire_event: True


add auth {{ mds }}:
  cmd.run:
    - name: "ceph auth add mds.{{ mds }} -i /var/lib/ceph/mds/ceph-{{ grains['host'] }}/keyring"

{% endfor %}

