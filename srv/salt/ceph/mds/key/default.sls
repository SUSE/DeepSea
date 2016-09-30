
prevent empty rendering:
  test.nop:
    - name: skip

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='mds', host=True) %}
{% set client = "mds." + host %}
{% set keyring_file = salt['keyring.file']('mds', host)  %}
{{ keyring_file}}:
  file.managed:
    - source: 
      - salt://ceph/mds/files/keyring.j2
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


