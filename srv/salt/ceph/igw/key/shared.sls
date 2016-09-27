
{% set keyring_file = salt['keyring.file']('igw', 'client.igw')  %}
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
      client: client.igw
      secret: {{ salt['keyring.secret'](keyring_file) }}

