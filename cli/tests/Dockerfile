FROM opensuse:42.3

LABEL maintainer="rdias@suse.com"

RUN zypper -n in glibc-locale jq vim
RUN zypper -n in --oldpackage salt-master=2016.11.4 salt-minion=2016.11.4
RUN sed -i -e 's/#master: salt/master: localhost/g' /etc/salt/minion
RUN sed -i -e 's!#extension_modules: .*!extension_modules: /srv/modules!g' /etc/salt/master
RUN zypper -n in python-setuptools python-click python-pytest \
                 python-coverage python-pytest-cov python-six

ADD start.sh /

ENV LANG "en_US.UTF-8"

ENTRYPOINT ["/start.sh"]
