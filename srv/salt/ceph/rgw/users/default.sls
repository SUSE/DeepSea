{% set os = salt['grains.get']('os') %}
{% set osmajorrelease = salt['grains.get']('osmajorrelease') %}

install rgw:
  pkg.installed:
    - pkgs:
      - ceph-radosgw
{% if ( osmajorrelease|int > 12 and osmajorrelease|int != 42 ) or ( os == 'CentOS' and osmajorrelease|int > 6 ) %}
      - python2-boto
{% else %}
      - python-boto
{% endif %}
    - refresh: True

add users:
  module.run:
    - name: rgw.add_users
