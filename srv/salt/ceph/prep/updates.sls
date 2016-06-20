
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

reboot:
  cmd.run:
    - name: "shutdown -r"
    - shell: /bin/bash
    - unless: "rpm -q --last kernel-default | head -1 | grep -q {{ kernel }}"


