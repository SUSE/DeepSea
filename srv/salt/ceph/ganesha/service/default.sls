{% if grains.get('os', '') == 'CentOS' %}

# for some reason the systemd service for nfs-ganesha is not working properly
# for CentOS, and therefore we are starting the service manually
start-ganesha:
  cmd.run:
    - name: "/usr/bin/ganesha.nfsd -L /var/log/ganesha/ganesha.log -f /etc/ganesha/ganesha.conf -N NIV_EVENT"
    - shell: /bin/bash
    - unless: "pgrep ganesha.nfsd"

{% else %}

start-ganesha:
  cmd.run:
    - name: "systemctl restart nfs-ganesha"
    - shell: /bin/bash

enable-ganesha:
  cmd.run:
    - name: "systemctl enable nfs-ganesha"
    - shell: /bin/bash

{% endif %}
