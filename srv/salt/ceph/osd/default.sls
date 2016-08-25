
include:
  - .keyring

{% for device in salt['pillar.get']('storage:osds') %}
prepare {{ device }}:
  module.run:
    - name: ceph.osd_prepare
    - kwargs: {
        osd_dev: {{ device }},
        }

activate {{ device }}:
  module.run:
    - name: ceph.osd_activate
    - kwargs: {
        osd_dev: {{ device }}
        }
    - fire_event: True

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
    - fire_event: True

activate {{ device }}:
  module.run:
    - name: ceph.osd_activate
    - kwargs: {
        osd_dev: {{ data }}
        }
    - fire_event: True

{% endfor %}
{% endfor %}

