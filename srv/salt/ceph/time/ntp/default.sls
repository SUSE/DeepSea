
{% set time_server = salt['pillar.get']('time_server') %}
{% if time_server is string %}
{% set time_server = [time_server] %}
{% endif %}

ntp:
  pkg.installed:
    - pkgs:
      - ntp
    - refresh: True

{% if salt['service.status']('ntpd') == False %}
sync time:
  cmd.run:
    - name: "sntp -S -c {{ time_server[0] }}"
{% endif %}

{% if grains['id'] not in salt['pillar.get']('time_server') %}
/etc/ntp.conf:
  file:
    - managed
    - source:
        - salt://ceph/time/ntp/files/ntp.conf.j2
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - backup: minion
    - fire_event: True

start ntp:
  service.running:
    - name: ntpd
    - enable: True
{% endif %}

