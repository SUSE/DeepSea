


{% set kernel= grains['kernelrelease'] | replace('-default', '')  %}

reboot:
  cmd.run:
    - name: "shutdown -r now"
    - shell: /bin/bash
    - unless: "rpm -q --last kernel-default | head -1 | grep -q {{ kernel }}"
    - failhard: True
    - order: 30
    - fire_event: True



