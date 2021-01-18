FROM fnndsc/ubuntu-python3:latest
LABEL MAINTAINER="dev@babymri.org"

# pfurl dependencies
RUN apt-get update \
  && apt-get install -qq libssl-dev libcurl4-openssl-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/local/src
COPY . .

RUN ["pip", "install", "."]

ENTRYPOINT ["pfioh"]
CMD ["--forever", "--httpResponse", "--createDirsAsNeeded"]
EXPOSE 5055
