
{% if grains.get('osfullname', '') == 'SLES' %}
hotfix for salt versioning:
  pkg.installed:
    - pkgs:
      - ses-release
{% endif %}
