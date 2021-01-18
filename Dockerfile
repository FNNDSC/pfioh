FROM python:3.9.1-buster
LABEL version="3.0.1" maintainer="FNNDSC <dev@babyMRI.org>" 

WORKDIR /usr/local/src
COPY requirements.txt .
RUN ["pip", "install", "-r", "requirements.txt"]
COPY . .
RUN ["pip", "install",  "."]

ENTRYPOINT ["pfioh"]
CMD ["--forever", "--httpResponse", "--createDirsAsNeeded"]
EXPOSE 5055
