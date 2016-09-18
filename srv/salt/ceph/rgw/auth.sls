

{% for config in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}

keyring {{ config }}:
  file.managed:
    - name: /var/lib/ceph/radosgw/{{ pillar.get('cluster') }}-{{ config }}/ceph.keyring
    - source:
      - salt://ceph/rgw/files/keyring.j2
    - template: jinja
    - user: ceph
    - group: ceph
    - mode: 600
    - makedirs: True
    - context:
        config : {{ config }}
    - fire_event: True


add auth {{ config }}:
  cmd.run:
    - name: "ceph auth add client.{{ config }}  -i /var/lib/ceph/radosgw/{{ pillar.get('cluster') }}-{{ config }}/ceph.keyring"

{% endfor %}
