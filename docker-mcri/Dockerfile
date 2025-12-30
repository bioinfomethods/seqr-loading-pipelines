FROM gcr.io/seqr-project/seqr-pipeline-runner:latest

COPY README* *build.d /build.d/
RUN bash -c 'for i in $(ls /build.d/*.sh 2>/dev/null | sort) ; do source $i ; done'

CMD [ "bash" ]

