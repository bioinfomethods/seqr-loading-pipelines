FROM bitnami/minideb:bullseye

LABEL maintainer="Broad TGG"

# install commmon utilities
RUN install_packages \
    ca-certificates \
    less \
    nano \
    wget \
    curl \
    emacs \
    g++ \
    git \
    htop \
    make \
    autoconf \
    unzip \
    bzip2 \
    zlib1g-dev \
    dpkg-dev \
    build-essential \
    libcurl4-openssl-dev \
    libbz2-dev \
    liblzma-dev

RUN apt-get update \
	&& apt-get dist-upgrade -y \
	&& apt-get install -y --no-install-recommends libncursesw5-dev libgdbm-dev libc6-dev zlib1g-dev libsqlite3-dev libssl-dev openssl libffi-dev sudo \
	&& apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN install_packages ca-certificates-java && install_packages default-jdk

ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PYTHON_VERSION="3.9.18"
ENV PYTHON_RELEASE="3.9"

RUN wget https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz \
	&& tar xvf Python-${PYTHON_VERSION}.tar.xz \
	&& rm Python-${PYTHON_VERSION}.tar.xz
WORKDIR /Python-${PYTHON_VERSION}
RUN ./configure --enable-optimizations \
    && make install \
    && make clean
WORKDIR /

RUN install_packages python-pkg-resources

# install gcloud tools
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --no-cache-dir -U crcmod

ENV GCLOUD_CLI_VERSION="454.0.0"
ENV CLOUDSDK_PYTHON=python3
RUN wget https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-${GCLOUD_CLI_VERSION}-linux-x86_64.tar.gz
RUN tar xzf google-cloud-cli-${GCLOUD_CLI_VERSION}-linux-x86_64.tar.gz && rm google-cloud-cli-${GCLOUD_CLI_VERSION}-linux-x86_64.tar.gz
RUN /google-cloud-sdk/install.sh -q

# python packages
RUN python3 -m pip install --upgrade gsutil

# install GCS connector using the same steps as in https://raw.githubusercontent.com/broadinstitute/install-gcs-connector/master/install_gcs_connector.py
# assumes ~/.config/gcloud/application_default_credentials.json will be mounted into the docker container
RUN python3 -m pip install hail
COPY docker/spark-defaults.conf /usr/local/lib/python${PYTHON_RELEASE}/site-packages/pyspark/conf/spark-defaults.conf
RUN wget https://repo1.maven.org/maven2/com/google/cloud/bigdataoss/gcs-connector/hadoop2-2.2.9/gcs-connector-hadoop2-2.2.9-shaded.jar -O /usr/local/lib/python${PYTHON_RELEASE}/site-packages/pyspark/jars/gcs-connector-hadoop2-2.2.9-shaded.jar

# install htslib
ENV SAMTOOLS_VERSION="1.18"
RUN wget https://github.com/samtools/htslib/releases/download/${SAMTOOLS_VERSION}/htslib-${SAMTOOLS_VERSION}.tar.bz2 \
	&& tar xjf htslib-${SAMTOOLS_VERSION}.tar.bz2 \
	&& rm htslib-${SAMTOOLS_VERSION}.tar.bz2
WORKDIR htslib-${SAMTOOLS_VERSION}
RUN ./configure \
	&& make \
	&& make install \
	&& make clean
WORKDIR /

# install VEP dependencies
RUN wget https://raw.github.com/miyagawa/cpanminus/master/cpanm -O /usr/bin/cpanm && chmod +x /usr/bin/cpanm
ENV VEP_VERSION="106"
RUN wget https://github.com/Ensembl/ensembl-vep/archive/release/${VEP_VERSION}.zip \
    && unzip ${VEP_VERSION}.zip \
    && rm ${VEP_VERSION}.zip

RUN /usr/bin/cpanm --notest Module::Build
RUN /usr/bin/cpanm --notest Set::IntervalTree
RUN /usr/bin/cpanm --notest PerlIO::gzip
RUN /usr/bin/cpanm --notest DBI
RUN /usr/bin/cpanm --notest CGI
RUN /usr/bin/cpanm --notest JSON
RUN /usr/bin/cpanm --notest Try::Tiny
# LoFTEE dependencies
RUN /usr/bin/cpanm --notest DBD::SQLite
RUN /usr/bin/cpanm --notest  List::MoreUtils

# install VEP
WORKDIR /ensembl-vep-release-${VEP_VERSION}
RUN perl INSTALL.pl -a ap -n -l -g all
RUN ln -s /ensembl-vep-release-${VEP_VERSION}/vep /vep

WORKDIR /seqr-loading-pipelines
COPY requirements.txt .
RUN python3 -m pip install -r ./requirements.txt

# copy files from seqr-loading-pipelines repo
COPY hail_builds/ ./hail_builds
COPY hail_scripts/ ./hail_scripts
COPY luigi_pipeline/ ./luigi_pipeline

COPY docker/vep_configs/* /vep_configs/

COPY docker/bashrc /root/.bashrc
COPY docker/gitconfig /root/.gitconfig
COPY docker/bin/*.sh /usr/local/bin/

ENV PATH=/usr/local/lib/python${PYTHON_RELEASE}/site-packages/pyspark/bin:/google-cloud-sdk/bin:$PATH
ENV PYTHONPATH=".:/seqr-loading-pipelines:/seqr-loading-pipelines/luigi_pipeline"

COPY docker/entrypoint.sh /

WORKDIR /

CMD [ "/entrypoint.sh" ]
