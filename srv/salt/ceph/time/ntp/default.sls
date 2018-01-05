
{% set time_server = salt['pillar.get']('time_server') %}
{% if time_server is string %}
{% set time_server = [time_server] %}
{% endif %}

install_ntp_packages:
  pkg.installed:
    - pkgs:
      - ntp
{% if grains.get('os', '') == 'CentOS' %}
      - sntp
{% endif %}
    - refresh: True
    - fire_event: True

service_reload:
  module.run:
    - name: service.systemctl_reload

{% if salt['service.status']('ntpd') == False %}
sync time:
  cmd.run:
  {% if grains.get('os_family', '') == 'Suse' %}
    - name: "sntp -S -c {{ time_server[0] }}"
  {% else %}
    - name: "sntp {{ time_server[0] }}"
  {% endif %}
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
    - fire_event: True
{% endif %}

