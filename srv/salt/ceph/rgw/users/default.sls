
{% for user in salt['pillar.get']('rgw_users', [ 'demo' ]) %}
user {{ user }}:
  cmd.run:
    - name: "radosgw-admin user create --uid={{ user }} --display-name={{ user }} > /srv/salt/ceph/rgw/cache/user.{{ user }}.json"
{% endfor %}
