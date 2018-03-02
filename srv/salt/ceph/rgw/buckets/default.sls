{% set os = salt['grains.get']('os') %}
{% set osmajorrelease = salt['grains.get']('osmajorrelease') %}

install rgw:
  pkg.installed:
    - pkgs:
{% if ( osmajorrelease|int > 12 and osmajorrelease|int != 42 ) or ( os == 'CentOS' and osmajorrelease|int > 6 ) %}
      - python2-boto
{% else %}
      - python-boto
{% endif %}
    - refresh: True

{% for user in salt['rgw.users'](contains="demo") %}
create demo bucket for {{ user }}:
  module.run:
    - name: rgw.create_bucket
    - kwargs:
        'user': {{user}}
        'bucket_name': {{ user }}-demo
{% endfor %}
