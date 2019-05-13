{% set ip_addresses = salt.saltutil.runner('select.public_addresses', roles_or=['mgr', 'igw'], cluster='ceph') | join(',') %}
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

{% if pillar.get('ceph_iscsi_ssl', False) %}
{% if pillar.get('ceph_iscsi_ssl_cert', None) and pillar.get('ceph_iscsi_ssl_key', None) %}

/srv/salt/ceph/igw/cache/tls/certs/iscsi-gateway.crt:
  file.managed:
    - source: {{ pillar['ceph_iscsi_ssl_cert'] }}
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - makedirs: True
    - fire_event: True

/srv/salt/ceph/igw/cache/tls/certs/iscsi-gateway.key:
  file.managed:
    - source: {{ pillar['ceph_iscsi_ssl_key'] }}
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - makedirs: True
    - fire_event: True

{% else %}

{% set CN = salt['deepsea.ssl_cert_cn_wildcard']() %}

/srv/salt/ceph/igw/cache/tls/certs/iscsi-gateway.crt:
  file.managed:
    - source: /etc/ssl/deepsea/certs/{{ CN }}.crt
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - makedirs: True
    - replace: True
    - fire_event: True

/srv/salt/ceph/igw/cache/tls/certs/iscsi-gateway.key:
  file.managed:
    - source: /etc/ssl/deepsea/certs/{{ CN }}.key
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - makedirs: True
    - replace: True
    - fire_event: True

{% endif %}
{% endif %}

fix salt job cache permissions:
  cmd.run:
  - name: "find /var/cache/salt/master/jobs -user root -exec chown {{ salt['deepsea.user']() }}:{{ salt['deepsea.group']() }} {} ';'"
