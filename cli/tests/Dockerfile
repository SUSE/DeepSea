FROM opensuse:tumbleweed

LABEL maintainer="rdias@suse.com"

RUN zypper -n in glibc-locale jq vim
RUN zypper -n in salt-master salt-minion
RUN sed -i -e 's/#master: salt/master: localhost/g' /etc/salt/minion
RUN sed -i -e 's!#extension_modules: .*!extension_modules: /srv/modules!g' /etc/salt/master
RUN zypper -n in python3-setuptools python3-click python3-pytest \
                 python3-coverage python3-pytest-cov

ADD start.sh /

ENV LANG "en_US.UTF-8"

ENTRYPOINT ["/start.sh"]
