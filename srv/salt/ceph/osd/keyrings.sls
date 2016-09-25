

{% set keyring_file = "/srv/salt/ceph/osd/cache/bootstrap.keyring" %}
{{ keyring_file}}:
  file.managed:
    - source: 
      - salt://ceph/osd/files/keyring.j2
    - template: jinja
    - user: salt
    - group: salt
    - mode: 600
    - makedirs: True
    - context:
      secret: {{ salt['keyring.secret'](keyring_file) }}
    - fire_event: True

auth {{ keyring_file }}:
  cmd.run:
    - name: "ceph auth add client.bootstrap-osd -i {{ keyring_file }}"


