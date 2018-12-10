
redeploy:
  module.run:
    - name: osd.redeploy
    - kwargs:
        timeout: 3600
        delay: 60

save grains:
  module.run:
    - name: osd.retain

