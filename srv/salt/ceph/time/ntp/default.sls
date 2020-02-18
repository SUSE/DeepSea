
ntp:
  pkg.installed:
    - pkgs:
      - ntp
    - refresh: True

{% if salt['service.status']('ntpd') == False %}
sync time:
  cmd.run:
    - name: "sntp -S -c {{ salt['pillar.get']('time_server') }}"
{% endif %}

{% if grains['id'] != salt['pillar.get']('time_server') %}
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
  cmd.run:
    - name: "systemctl enable ntpd.service && systemctl start ntpd.service"
{% endif %}

