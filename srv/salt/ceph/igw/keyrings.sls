
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='igw', host=True) %}
{% set client = "client.igw." + host %}
{% set keyring_file = "/srv/salt/ceph/iscsi/cache/ceph." +  client + ".keyring" %}
{{ keyring_file}}:
  file.managed:
    - source: 
      - salt://ceph/iscsi/files/keyring.j2
    - template: jinja
    - user: salt
    - group: salt
    - mode: 600
    - makedirs: True
    - context:
      client: {{ client }}
      secret: {{ salt['keyring.secret'](keyring_file) }}

auth {{ keyring_file }}:
  cmd.run:
    - name: "ceph auth add {{ client }} -i {{ keyring_file }}"

{% endfor %}
