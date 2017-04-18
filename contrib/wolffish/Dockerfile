FROM opensuse:tumbleweed
RUN zypper --non-interactive install git npm4 hostname
RUN npm install -g bower
RUN npm install -g polymer-cli
RUN git clone https://github.com/kmroz/wolffish.git /opt/wolffish
WORKDIR /opt/wolffish
RUN bower --allow-root install
CMD polymer serve --hostname `hostname -i`
