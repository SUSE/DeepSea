{% set ip_addresses = salt.saltutil.runner('select.public_addresses', roles_or=['mgr', 'igw'], cluster='ceph') | join(', ') %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='igw', host=True) %}
/srv/salt/ceph/igw/cache/iscsi-gateway.{{ host }}.cfg:
  file.managed:
    - source: salt://ceph/igw/files/iscsi-gateway.cfg.j2
    - template: jinja
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 644
    - makedirs: True
    - fire_event: True
    - context:
        client: "client.igw.{{ host }}"
        trusted_ip_list: {{ ip_addresses }}
{% endfor %}

fix salt job cache permissions:
  cmd.run:
  - name: "find /var/cache/salt/master/jobs -user root -exec chown {{ salt['deepsea.user']() }}:{{ salt['deepsea.group']() }} {} ';'"
  