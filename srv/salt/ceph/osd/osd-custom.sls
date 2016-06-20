
include:
  - .partition

{% for device in salt['pillar.get']('storage:osds') %}
prepare {{ device }}:
  module.run:
    - name: ceph.osd_prepare
    - kwargs: {
        osd_dev: {{ device }}2,
        journal_dev: {{ device }}1
        }
    - require:
      - module: keyring_osd_auth_add

activate {{ device }}:
  module.run:
    - name: ceph.osd_activate
    - kwargs: {
        osd_dev: {{ device }}2
        }

{% endfor %}

{% for pair in salt['pillar.get']('storage:data+journals') %}
{% for data, journal in pair.items() %}
prepare {{ data }}:
  module.run:
    - name: ceph.osd_prepare
    - kwargs: {
        osd_dev: {{ data }},
        journal_dev: {{ journal }}
        }
    - require:
      - module: keyring_osd_auth_add

activate {{ device }}:
  module.run:
    - name: ceph.osd_activate
    - kwargs: {
        osd_dev: {{ data }}
        }

{% endfor %}
{% endfor %}


