{% set dashboard_user = salt['pillar.get']('dashboard_user', 'admin') %}
{% set dashboard_pw = salt['pillar.get']('dashboard_password', salt['grains.get']('dashboard_creds:' ~ dashboard_user , salt['random.get_str'](10))) %}
{% set dashboard_ssl = salt['pillar.get']('dashboard_ssl', True) %}
{% set dashboard_ssl_cert = salt['pillar.get']('dashboard_ssl_cert', None) %}
{% set dashboard_ssl_key = salt['pillar.get']('dashboard_ssl_key', None) %}

{% if not dashboard_ssl %}
disable dashboard ssl:
  cmd.run:
    - name: ceph config set mgr mgr/dashboard/ssl false
    - failhard: True
    - fire_event: True

set dashboard port:
  cmd.run:
    - name: ceph config set mgr mgr/dashboard/server_port {{ salt['pillar.get']('dashboard_port', 8080) }}
    - failhard: true
    - fire_event: True
{% else %}
set dashboard ssl port:
  cmd.run:
    - name: ceph config set mgr mgr/dashboard/ssl_server_port {{ salt['pillar.get']('dashboard_ssl_port', 8443) }}
    - failhard: true
    - fire_event: True
{% endif %}

enable ceph dashboard:
  cmd.run:
    - name: ceph mgr module enable dashboard
    - failhard: True

{% if dashboard_ssl %}
{% if dashboard_ssl_cert and dashboard_ssl_key %}
set dashboard ssl cert:
  cmd.run:
    - name: ceph config-key set mgr/dashboard/crt -i {{ dashboard_ssl_cert }}
    - failhard: True
    - fire_event: True

set dashboard ssl key:
  cmd.run:
    - name: ceph config-key set mgr/dashboard/key -i {{ dashboard_ssl_key }}
    - failhard: True
    - fire_event: True

{% else %}

{% set CN = salt['deepsea.ssl_cert_cn_wildcard']() %}

set dashboard ssl cert:
  cmd.run:
    - name: ceph config-key set mgr/dashboard/crt -i /etc/ssl/deepsea/certs/{{ CN }}.crt
    - failhard: True
    - fire_event: True

set dashboard ssl key:
  cmd.run:
    - name: ceph config-key set mgr/dashboard/key -i /etc/ssl/deepsea/certs/{{ CN }}.key
    - failhard: True
    - fire_event: True

{% endif %}
{% endif %}

dashboard user exists:
  cmd.run:
    - name: /bin/true
    - unless: ceph dashboard ac-user-show -f json | jq -e 'index("{{ dashboard_user }}")'

set username and password:
  cmd.run:
    # This command is printed although the 'onchange' statement evaluates as true. This might cause confusion.
    - name: "echo -n {{ dashboard_pw }} | ceph dashboard ac-user-create {{ dashboard_user }} -i - administrator"
    - onchanges:
        - cmd: dashboard user exists

set dashboard password grain:
  module.run:
    - name: grains.set
    - key: dashboard_creds:{{ dashboard_user }}
    - val: {{ dashboard_pw }}
    - onchanges:
        - cmd: set username and password

# configure grafana
{% set grafana_default = salt.saltutil.runner('select.one_minion', cluster='ceph', roles='grafana') %}
{% set grafana_minion = salt['pillar.get']('GRAFANA_MINION', grafana_default) %}
{% if grafana_minion %}
set dashboard grafana url:
  cmd.run:
    - name: ceph dashboard set-grafana-api-url https://{{ grafana_minion }}:3000
    - fire_event: True
{% endif %}
