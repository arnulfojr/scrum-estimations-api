#!/usr/bin/env sh

# Run all the scripts within the specified life cycle
# We execute everything that is executable within the life cycle's directory
execute_life_cyle() {
  life_cycle_name=${1:?'Please provide the name of the life cycle to run'}

  cycle_does_not_exists="$(life_cycle_exists "${life_cycle_name}")"
  if [ "${cycle_does_not_exists}" = '1' ]; then
    echo "...... Life cycle ${life_cycle_name} does not exist"
    exit 1
  else
    echo "...... Running life cycle ${life_cycle_name}"
  fi

  full_life_cycle_path="${SCRIPT_DIRECTORY}/${life_cycle_name}/*"
  echo "...... Running scripts within ${full_life_cycle_path}"

  for f in ${full_life_cycle_path}; do
    if [ -f "${f}" ] && [ -x "${f}" ]; then
      echo "...... FILE: ${f}"
      # shellcheck disable=SC1090
      . "${f}"
    else
      echo "...... IGNORING: ${f}"
    fi
  done
}

# Returns a binary result wheter the specified lifecycle exists or not
life_cycle_exists () {
  life_cycle_name=${1:?'Please provide the name of the life cycle to check'}

  if [ ! -f "${SCRIPT_DIRECTORY}/${life_cycle_name}" ]; then
    return 0
  else
    return 1
  fi
}

normalize_ci_variables() {
  REPO_NAME=
  if [ -n "${CI_REPO_NAME}" ]; then
    REPO_NAME="$( echo "${CI_REPO_NAME}" | cut -d'/' -f2 )"
  else
    REPO_NAME='my-default-app'
  fi
  export REPO_NAME
  echo "... Exported REPO_NAME=${REPO_NAME}"

  ARTIFACT_TAG=
  if [ -n "${CI_COMMIT_BRANCH}" ] && [ -n "${CI_COMMIT_SHA}" ]; then
    normalized_branch_name="$( echo "${CI_COMMIT_BRANCH}" | cut -d'/' -f2 )"
    ARTIFACT_TAG="${normalized_branch_name}-${CI_COMMIT_SHA}"
  else
    ARTIFACT_TAG='local'
  fi
  export ARTIFACT_TAG
  echo "... Exported ARTIFACT_TAG=${ARTIFACT_TAG}"

  PROJECT_DIRECTORY=
  if [ -z "${PROJECT_DIRECTORY}" ]; then
    PROJECT_DIRECTORY="${PWD}"
  fi
  if [ -n "${CI_WORKSPACE}" ]; then
    PROJECT_DIRECTORY="${CI_WORKSPACE}"
  fi
  export PROJECT_DIRECTORY
  echo "... Exported PROJECT_DIRECTORY=${PROJECT_DIRECTORY}"
}

assert_vars_exists() {
  for arg in "${@}"; do
    eval "val=\$${arg}"
    # shellcheck disable=SC1009,SC2154
    if [ -z "${val}" ]; then
      echo "... Failed to assure that ${arg} was present in the environment"
      exit 1
    else
      echo "... ${arg} is present"
    fi
  done
}

source_service_env_file() {
  if [ -f "${PROJECT_DIRECTORY}/service.env" ]; then
    echo "... Importing ${PROJECT_DIRECTORY}/service.env"
    cat "${PROJECT_DIRECTORY}"/service.env
    # shellcheck disable=SC1090
    . "${PROJECT_DIRECTORY}"/service.env
  else
    echo "... No ${PROJECT_DIRECTORY}/service.env file was found"
  fi
}
