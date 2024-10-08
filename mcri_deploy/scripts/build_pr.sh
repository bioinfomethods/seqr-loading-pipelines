#!/bin/bash
#
# Launch archie agent and run as daemon using jsvc

set -eo pipefail

#######################################
# info() and error() log messages to STDOUT and STDERR respectively.
# Globals:
#   None
# Arguments:
#   Variable args written out as string
# Outputs:
#   Writes message to STDOUT or STDERR
#######################################
function info() {
    echo "[$(date +'%Y-%m-%dT%H:%M:%S%z') INFO $(basename "$0")] $*" >&1
}

function error() {
    echo "[$(date +'%Y-%m-%dT%H:%M:%S%z') ERROR $(basename "$0")] $*" >&2
}

function usage() {
    info "usage: build_pr.sh {test|prod|info}"
}

check_command() {
    if ! command -v "$1" &> /dev/null
    then
        error "$1 could not be found"
        exit 3
    fi
}

check_command "git"
check_command "docker"

if [ -z "$1" ]; then
    usage
    exit 3
fi

if [ -z "$2" ]; then
    BUILD_OPTS="--progress auto"
else
    BUILD_OPTS="--progress auto $2"
fi

set -euo pipefail

build() {
    PROJECT_DIR="$HOME/$1"
    if [ ! -d "$PROJECT_DIR" ]; then
      error "$PROJECT_DIR does not exist"
      exit 3
    fi
    cd "$PROJECT_DIR"
    info "Running build for $PROJECT_DIR"

    git pull

    COMPOSE_FILE="$PROJECT_DIR/mcri_deploy/docker-compose/docker-compose.yml"
    COMPOSE_BUILD_FILE="$PROJECT_DIR/mcri_deploy/docker-compose/docker-compose.build.yml"

    cp "$PROJECT_DIR/.env.template" "$PROJECT_DIR/.env"
    COMPOSE_ENV_FILE="$PROJECT_DIR/.env"
    
    for line in $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
    do
        eval "$line"
    done

    # Tagging
    SLP_GIT_BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)
    SLP_GIT_BRANCH_TAG=${SLP_GIT_BRANCH_NAME/\//_}
    SLP_LONG_GIT_TAG=$(git describe --long --always)

    build_pr "$@"
}

build_pr() {
    info "Building pipeline-runner component only, BUILD_OPTS=$BUILD_OPTS"
    set -x
    docker compose --verbose \
      -f "$COMPOSE_FILE" \
      -f "$COMPOSE_BUILD_FILE" \
      --env-file="$COMPOSE_ENV_FILE" \
      build $BUILD_OPTS pipeline-runner

    docker compose --verbose \
      -f "$COMPOSE_FILE" \
      -f "$COMPOSE_BUILD_FILE" \
      --env-file="$COMPOSE_ENV_FILE" \
      push pipeline-runner

    docker tag "$CONTAINER_REGISTRY/$PIPELINE_RUNNER_IMAGE_NAME:$PIPELINE_RUNNER_IMAGE_TAG" "$CONTAINER_REGISTRY/$PIPELINE_RUNNER_IMAGE_NAME:$SLP_GIT_BRANCH_TAG"
    docker push "$CONTAINER_REGISTRY/$PIPELINE_RUNNER_IMAGE_NAME:$SLP_GIT_BRANCH_TAG"

    docker tag "$CONTAINER_REGISTRY/$PIPELINE_RUNNER_IMAGE_NAME:$PIPELINE_RUNNER_IMAGE_TAG" "$CONTAINER_REGISTRY/$PIPELINE_RUNNER_IMAGE_NAME:$SLP_LONG_GIT_TAG"
    docker push "$CONTAINER_REGISTRY/$PIPELINE_RUNNER_IMAGE_NAME:$SLP_LONG_GIT_TAG"

    if [[ "$1" == "seqr-loading-pipelines" ]]; then
        SLP_VERSION="$(git describe --always)"
        docker tag "$CONTAINER_REGISTRY/$PIPELINE_RUNNER_IMAGE_NAME:$PIPELINE_RUNNER_IMAGE_TAG" "$CONTAINER_REGISTRY/$PIPELINE_RUNNER_IMAGE_NAME:$SLP_VERSION"
        docker push "$CONTAINER_REGISTRY/$PIPELINE_RUNNER_IMAGE_NAME:$SLP_VERSION"
    fi
}

case "$1" in
test)
    build "seqr-loading-pipelines-test"
    ;;
prod)
    build "seqr-loading-pipelines"
    ;;
*)
    usage
    exit 3
    ;;
esac
