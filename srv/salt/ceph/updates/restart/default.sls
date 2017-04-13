# to avoid rebooting twice also check if update_method_init != 'patch'
{% if salt['pillar.get']('auto_reboot', True) == True and salt['pillar.get']('update_method_init', default) != 'default' %}

{% set kernel = grains['kernelrelease'] | replace('-default', '')  %}
{% set installed = salt['cmd.run']('rpm -q --last kernel-default | head -1 | cut -f1 -d\  ') | replace('kernel-default-', '') %}

warning:
  module.run:
    - name: advise.reboot
    - running: {{ kernel }}
    - installed: {{ installed }}
    - unless: "echo {{ installed }} | grep -q {{ kernel }}"

reboot:
  cmd.run:
    - name: "shutdown -r now"
    - shell: /bin/bash
    - unless: "echo {{ installed }} | grep -q {{ kernel }}"
    - failhard: True
    - fire_event: True

{% else %}

prevent empty rendering:
  test.nop:
    - name: skip

{% endif %}
