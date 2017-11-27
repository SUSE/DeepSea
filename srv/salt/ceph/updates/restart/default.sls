
{% set kernel = grains['kernelrelease'] | replace('-default', '')  %}
{% set installed = salt['kernel.installed_kernel_version']() %}

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

