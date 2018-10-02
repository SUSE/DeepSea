
{% for id in salt['osd.list']() %}

starting {{ id }}:
  service.running:
    - name: ceph-osd@{{ id }}

{% endfor %}

