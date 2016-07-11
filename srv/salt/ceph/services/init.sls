
iSCSI:
  salt.runner:
    - name: push.proposal

post configuration:
  salt.runner:
    - name: configure.cluster

{# likely need a validate here if anything has been disabled #}

