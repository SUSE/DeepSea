
{% for device in salt['pillar.get']('storage:osds') %}
{{ device }} journal:
  module.run:
    - name: partition.mkpart
    - device: {{ device }}
    - part_type: primary
    - start: 0%
    - end: 10%
    - require:
      - module: {{ device }} label
    - unless: stat {{ device }}1

{{ device }} journal uuid:
  cmd.run:
    - name: "sgdisk -t 1:45b0969e-9b03-4f30-b4c6-b4b80ceff106 {{ device }}"
    - unless: "sgdisk -i 1 {{ device }} | grep -q unique.*45b0969e-9b03-4f30-b4c6-b4b80ceff106$"

{{ device }} data:
  module.run:
    - name: partition.mkpart
    - device: {{ device }}
    - part_type: primary
    - start: 10%
    - end: 100%
    - require:
      - module: {{ device }} label
    - unless: stat {{ device }}2

{{ device }} uuid:
  cmd.run:
    - name: "sgdisk -t 2:4fbd7e29-9d25-41b8-afd0-062c0ceff05d {{ device }}"
    - unless: "sgdisk -i 2 {{ device }} | grep -q unique.*4fbd7e29-9d25-41b8-afd0-062c0ceff05d"

{{ device }} label:
  module.run:
    - name: partition.mklabel
    - device: {{ device }}
    - label_type: gpt
    - unless: blkid {{ device }} 

{% endfor %}

