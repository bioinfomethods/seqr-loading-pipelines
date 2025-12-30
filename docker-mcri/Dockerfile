FROM gcr.io/seqr-project/seqr-pipeline-runner:latest

ENV UV_NATIVE_TLS=true

COPY README* *build.d /build.d/
RUN bash -c 'for i in $(ls /build.d/*.sh 2>/dev/null | sort) ; do source $i ; done'

RUN uv sync

apt-get update

apt-get install -y vim htop ncdu

CMD [ "bash" ]

