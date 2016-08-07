
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

activate {{ device }}:
  module.run:
    - name: ceph.osd_activate
    - kwargs: {
        osd_dev: {{ data }}
        }

{% endfor %}
{% endfor %}

