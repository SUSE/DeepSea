{% if salt['pillar.get']('change_kernel') == 'YES' %}
{% set kernel_pkg = salt['pillar.get']('kernel_package') %}
{% set kernel_not_installed = salt['kernel.verify_kernel_installed'](
                 kernel_package=kernel_pkg) == False
%}

{% if kernel_not_installed %}

install kernel package:
  cmd.run:
    - name: "zypper --non-interactive --no-gpg-checks install --force-resolution {{ kernel_pkg }}"
    - shell: /bin/bash
    - unless: "rpm -q {{ kernel_pkg }}"
    - fire_event: True

warning reboot on install:
  cmd.run:
    - name: "echo 'Installed {{ kernel_pkg }} package, rebooting now...' | /usr/bin/wall"
    - shell: /bin/bash
    - failhard: True
    - fire_event: True

reboot on install:
  cmd.run:
    - name: "shutdown -r now"
    - shell: /bin/bash
    - failhard: True
    - fire_event: True

{% endif %}
{% endif %}

zypper update:
  cmd.run:
    - name: "zypper --non-interactive  update --replacefiles --auto-agree-with-licenses"
    - shell: /bin/bash
    - unless: "zypper lu | grep -sq 'No updates found'"

