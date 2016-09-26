
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='igw', host=True) %}
{% set client = "client.igw." + host %}
{% set keyring_file = salt['keyring.file']('igw', client)  %}
{{ keyring_file}}:
  file.managed:
    - source: 
      - salt://ceph/igw/files/keyring.j2
    - template: jinja
    - user: salt
    - group: salt
    - mode: 600
    - makedirs: True
    - context:
      client: {{ client }}
      secret: {{ salt['keyring.secret'](keyring_file) }}

{% endfor %}
