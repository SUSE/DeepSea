"salt-call pillar.items --out=yaml > /tmp/pillar-post-engulf.yml":
  cmd.run

# Seems to be the only way I can get a RuntimeError out of a module to die nicely
# and indicate test failur
"salt-call functest.verify_engulf":
  cmd.run
