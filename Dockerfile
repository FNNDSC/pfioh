#
# Dockerfile for pman repository.
#
# Build with
#
#   docker build -t <name> .
#
# For example if building a local version, you could do:
#
#   docker build -t local/pfioh .
#
# In the case of a proxy (located at 192.168.13.14:3128), do:
#
#    docker build --build-arg http_proxy=http://192.168.13.14:3128 -t local/pfioh .
#

FROM fnndsc/ubuntu-python3:latest
MAINTAINER fnndsc "dev@babymri.org"

RUN apt-get update \
  && apt-get install -y libssl-dev libcurl4-openssl-dev bsdmainutils vim \
  && pip3 install --prefix /usr pfioh==1.3.6 \
  && pip3 install pudb

COPY ./docker-entrypoint.py /dock/docker-entrypoint.py
RUN chmod 777 /dock && chmod 777 /dock/docker-entrypoint.py
ENTRYPOINT ["/dock/docker-entrypoint.py"]
EXPOSE 5055
