{% for id in salt['osd.list']() %}
taking over osd {{ id }}:
  cmd.run:
    - name: "ceph-volume simple scan /var/lib/ceph/osd/ceph-{{ id }}"

{% endfor %}
