# debian is preferred over alpine because in the strange
# tree of dependencies, pfmisc depends on numpy
FROM python:3.9.1-buster
LABEL version="3.0.1" maintainer="FNNDSC <dev@babyMRI.org>" 

WORKDIR /usr/local/src
COPY . .
RUN pip install .

ENTRYPOINT ["pfioh"]
CMD ["--forever", "--httpResponse", "--createDirsAsNeeded"]
EXPOSE 5055
