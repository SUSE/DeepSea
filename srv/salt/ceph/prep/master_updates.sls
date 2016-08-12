
zypper update:
  cmd.run:
    - name: "zypper --non-interactive update --replacefiles"
    - shell: /bin/bash
    - unless: "zypper lu | grep -sq 'No updates found'"

kernel update:
  cmd.run:
    - name: "zypper --non-interactive --no-gpg-checks up kernel-default"
    - shell: /bin/bash
    - unless: "zypper info kernel-default | grep -q '^Status: up-to-date'"

{% set kernel= grains['kernelrelease'] | replace('-default', '')  %}
{% set latest = salt['cmd.run']('rpm -q --last kernel-default | head -1', shell="/bin/bash" ) %}

{% if kernel not in latest %}
{% set marker = salt.saltutil.runner('filequeue.remove', queue='master', name='begin') %}

reboot:
  cmd.run:
    - name: "shutdown -r now"
    - shell: /bin/bash
    - failhard: True

{% endif %}


