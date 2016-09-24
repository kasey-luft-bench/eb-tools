#!/usr/bin/env bash

set -o errexit
set -o pipefail

_info () {
  echo "[info] $1"
}

_error () {
  echo "[error] $1"
}
_poll_endpoint () {
  local url="$1"
  while true; do
    curl --retry 10 --max-time 10 --fail --silent "$url" 2>&1> /dev/null \
      && break || sleep 10
  done
}

_list_environments () {
  local fields='ApplicationName, EnvironmentName, Status, Health, HealthStatus, VersionLabel, CNAME'
  echo "$fields" | sed 's/, /\t/g; s/\.//g'
  aws elasticbeanstalk describe-environments \
    --query "Environments[*].[$fields]" --output text \
    | sort
}

_list_events () {
  aws elasticbeanstalk describe-events --max-items 200 --severity INFO \
    | jq -r '.Events[] | [.EventDate, .Severity, .EnvironmentName // .ApplicationName, .Message] | join("§") | sub("\n"; " "; "g")' \
    | column -s '§' -t \
    | sort -r
}

_get_environment () {
  local application="$1"
  local environment="$2"
  local filters="$3"
  aws elasticbeanstalk describe-environments | jq --raw-output ".Environments[]
    | select (.ApplicationName == \"$application\")
    | select (.EnvironmentName == \"$environment\")
    | $filters"
}

_validate_url () {
  local url="$1"
  echo "$url" | grep 'elasticbeanstalk.com' 2>&1> /dev/null || _error "Invalid url."
}

_is_online () {
  local application="$1"
  local environment="$2"
  local endpoint="${3:-/api/heartbeat}"

  _info "Resolving URL for application: '$application' and environment '$environment'"
  local url="$(_get_environment "$application" "$environment" ".CNAME")${endpoint}"
  _validate_url "$url"

  _info "Querying \"$url\""
  _poll_endpoint "$url"

  _info "The environment is online."
}

_query_status () {
  local application="$1"
  local environment="$2"
  local criteria="${3:-ReadyGreen}"
  local status="$(_get_environment "$application" "$environment" '.Status + .Health')"

  _info "Status: '$status', expected: '$criteria'"
  if [[ -z "$status" ]]; then
    _info "Empty status, are application: '$application' and environment: '$environment' valid?"
    exit -1
  fi
  echo "$status" | grep "$criteria" 2>&1> /dev/null
}

_ready_and_green () {
  local application="$1"
  local environment="$2"
  while true; do
    _query_status "$application" "$environment" && break || sleep 10
  done
  _info "Environment is ready and green!"
}

_usage () {
  echo "Usage: $0 [arg...]"
  echo "You can pass in one of the following options:"
  echo "  --list                                       List all applications and environments, their health and other status."
  echo "  --events                                     List all events for every applications and environments."
  echo "  --status            APPLICATION ENVIRONMENT  Get environment status and health."
  echo "  --ready-and-green   APPLICATION ENVIRONMENT  Wait for environment to be green and ready."
  echo "  --is-online         APPLICATION ENVIRONMENT  Wait for environment's actual heartbeat endpoint to be alive."
  echo "  --ready-and-online  APPLICATION ENVIRONMENT  Wait for environment to be green, ready and actual heartbeat endpoint to be alive."
  echo "  --help                                       Print this help message."
}

opt="$1"
args=${@:2}

case "$opt" in
  --help)
    _usage
    ;;
  --status)
    _query_status $args
    ;;
  --ready-and-green)
    _ready_and_green $args
    ;;
  --is-online)
    _is_online $args
    ;;
  --ready-and-online)
    _ready_and_green $args
    _is_online $args
    ;;
  --list)
    _list_environments | column -t
    ;;
  --events)
    _list_events
    ;;
  *)
    _list_environments | column -t
    _usage
    exit -1
    ;;
esac
