
{% for config in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}
/var/lib/ceph/radosgw/{{ pillar.get('cluster') }}-{{ config }}/keyring:
  file.managed:
    - source:
      - salt://ceph/rgw/files/keyring.j2
    - template: jinja
    - user: salt
    - group: salt
    - mode: 600
    - makedirs: True
    - fire_event: True
    - context:
        config: {{ config }}
{% endfor %}
