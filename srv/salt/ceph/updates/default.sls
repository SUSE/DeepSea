
zypper update:
  cmd.run:
    - name: "zypper --non-interactive update --replacefiles"
    - shell: /bin/bash
    - unless: "zypper lu | grep -sq 'No updates found'"
    - order: 10
    - fire_event: True

kernel update:
  cmd.run:
    - name: "zypper --non-interactive --no-gpg-checks up kernel-default"
    - shell: /bin/bash
    - unless: "zypper info kernel-default | grep -q '^Status: up-to-date'"
    - require:
      - cmd: zypper update
    - order: 20
    - fire_event: True

{% set kernel= grains['kernelrelease'] | replace('-default', '')  %}

reboot:
  cmd.run:
    - name: "shutdown -r now"
    - shell: /bin/bash
    - unless: "rpm -q --last kernel-default | head -1 | grep -q {{ kernel }}"
    - failhard: True
    - require:
      - cmd: kernel update
    - order: 30
    - fire_event: True

nop:
  test.nop:
    - require:
      - cmd: kernel update


