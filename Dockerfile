FROM fnndsc/ubuntu-python3:ubuntu20.04-python3.8.5
LABEL version="3.0.2" maintainer="FNNDSC <dev@babyMRI.org>" 

WORKDIR /usr/local/src
COPY requirements.txt .
RUN ["pip", "install", "-r", "requirements.txt"]
COPY . .
RUN ["pip", "install",  "."]

ENTRYPOINT ["pfioh"]
CMD ["--forever", "--httpResponse", "--createDirsAsNeeded"]
EXPOSE 5055
