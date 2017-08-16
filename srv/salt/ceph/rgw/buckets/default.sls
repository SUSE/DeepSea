
install rgw:
  pkg.installed:
    - pkgs:
      - python-boto

{% for user in salt['rgw.users']('rgw') %}
create demo bucket for {{ user }}:
  module.run:
    - name: rgw.create_bucket
    - kwargs:
        'user': {{user}}
        'bucket_name': {{ user }}-demo
{% endfor %}
