# Include :download:`map file <map.jinja>` of OS-specific package names and
# file paths. Values can be overridden using Pillar.
{% from "ceph/time/ntp-formula/ntp/map.jinja" import ntp with context %}

ntp:
  pkg.installed:
    - name: {{ ntp.client }}

{% set time_server = salt['pillar.get']('time_service:ntp_server') %}
{% if time_server and time_server.startswith(grains['host']) %}
  {% set ntp_conf_file = salt['pillar.get']('time_service:ntp_server_conf','ntp-server-default.conf') %}
{% else %}
  {% set ntp_conf_file = salt['pillar.get']('time_service:ntp_client_conf','ntp-client-default.conf') %}
{% endif %}
{% set ntp_conf_src = ['salt://ceph/time/ntp-formula/ntp/', ntp_conf_file]|join %}

{% if ntp_conf_src %}
ntp_conf:
  file.managed:
    - name: {{ ntp.ntp_conf }}
    - template: jinja
    - source: {{ ntp_conf_src }}
    - require:
      - pkg: {{ ntp.client }}
{% endif %}

{% if ntp.ntp_conf -%}
ntp_running:
  service.running:
    - name: {{ ntp.service }}
    - enable: True
    - watch:
      - file: {{ ntp.ntp_conf }}
{% endif -%}
