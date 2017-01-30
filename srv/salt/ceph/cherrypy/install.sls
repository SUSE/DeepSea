
cherrypy:
  pkg.installed:
    - pkgs:
      - salt-api
    - fire_event: True

certificate:
  module.run:
    - name: tls.create_self_signed_cert

