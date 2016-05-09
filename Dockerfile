FROM ubuntu:14.04
MAINTAINER Huichao Xue

RUN apt-get update && apt-get install -y git build-essential python git python-nltk libboost-dev gfortran byacc bison python-dev python-scipy python-numpy

WORKDIR /maxent
RUN git clone https://github.com/lzhang10/maxent.git
WORKDIR /maxent/maxent
RUN ./configure && make && make install
WORKDIR /maxent/maxent/python
RUN python setup.py build && python setup.py install
RUN perl -pi -e 's#DEFAULT_URL = .*#DEFAULT_URL = "http://nltk.github.com/nltk_data/"#' /usr/lib/python2.7/dist-packages/nltk/downloader.py
RUN python -m nltk.downloader wordnet
RUN python -m nltk.downloader maxent_treebank_pos_tagger

ADD *.py /corr_det/
ADD *.txt /corr_det/
ADD *.c /corr_det/
ADD *.sh /corr_det/
ADD *.model /corr_det/

WORKDIR /corr_det
RUN ./compile_editdistalign.sh

RUN apt-get purge -y python-dev build-essential git libboost-dev gfortran byacc bison
RUN apt-get autoremove -y

EXPOSE 8085

CMD python /corr_det/server.py