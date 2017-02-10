

include:
  - .{{ salt['pillar.get']('cherrypy_init', 'default') }}

