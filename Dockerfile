# Dockerfile for pfioh production.
#
# Build with
#
#   docker build -t <name> .
#
# For example if building a local version, you could do:
#
#   docker build -t local/pfioh .
#
# In the case of a proxy (located at say 10.41.13.4:3128), do:
#
#    export PROXY="http://10.41.13.4:3128"
#    docker build --build-arg http_proxy=${PROXY} --build-arg UID=$UID -t local/pfioh .
#
# To run an interactive shell inside this container, do:
#
#   docker run -ti --rm --entrypoint /bin/bash local/pfioh
#
# To pass an env var HOST_IP to container, do:
#
#   docker run -ti --rm -e HOST_IP=$(ip route | grep -v docker | awk '{if(NF==11) print $9}') --entrypoint /bin/bash local/pfioh
#

FROM fnndsc/ubuntu-python3:latest
MAINTAINER fnndsc "dev@babymri.org"

# Pass a UID on build command line (see above) to set internal UID
ARG UID=1001
ENV UID=$UID DEBIAN_FRONTEND=noninteractive APPROOT="/home/localuser/pfioh"

RUN apt-get update \
  && apt-get install -y libssl-dev libcurl4-openssl-dev bsdmainutils net-tools inetutils-ping \
  && apt-get install -y libgnutls28-dev \
  && pip install --upgrade pip \
  && useradd -u $UID -ms /bin/bash localuser

# Copy source code
COPY --chown=localuser ./bin ${APPROOT}/bin
COPY --chown=localuser ./pfioh ${APPROOT}/pfioh
COPY --chown=localuser ./openshift ${APPROOT}/openshift
COPY --chown=localuser ./setup.cfg ./setup.py README.rst  ${APPROOT}/

RUN pip3 install ${APPROOT}  \
  && rm -fr ${APPROOT}

# Start as user localuser
#USER localuser

WORKDIR "/home/localuser"
ENTRYPOINT ["pfioh", "--forever", "--httpResponse", "--createDirsAsNeeded"]
EXPOSE 5055
