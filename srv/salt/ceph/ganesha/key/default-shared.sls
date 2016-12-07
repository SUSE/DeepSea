
{% for role in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}
{% set client = "client." + role %}
{% set keyring_file = salt['keyring.file']('rgw', client)  %}

check {{ role }}:
  file.exists:
    - name: /srv/salt/ceph/rgw/files/{{ role }}.j2
    - failhard: True

{{ keyring_file}}:
  file.managed:
    - source: 
      - salt://ceph/rgw/files/{{ role }}.j2
    - template: jinja
    - user: salt
    - group: salt
    - mode: 600
    - makedirs: True
    - context:
      client: {{ client }}
      secret: {{ salt['keyring.secret'](keyring_file) }}
    - fire_event: True

{% endfor %}


