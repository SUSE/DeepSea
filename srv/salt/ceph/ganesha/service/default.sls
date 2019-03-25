{% if grains.get('os', '') == 'CentOS' %}

# for some reason the systemd service for nfs-ganesha is not working properly
# for CentOS, and therefore we are starting the service manually
start-ganesha:
  cmd.run:
    - name: "/usr/bin/ganesha.nfsd -L /var/log/ganesha/ganesha.log -f /etc/ganesha/ganesha.conf -N NIV_EVENT"
    - shell: /bin/bash
    - unless: "pgrep ganesha.nfsd"

{% else %}

enable and start nfs-ganesha:
  service.running:
    - name: nfs-ganesha
    - enable: True
    - fire_event: True

{% endif %}
