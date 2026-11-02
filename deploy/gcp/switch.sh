#!/usr/bin/env bash
# Switch gcloud between projects (and the accounts that own them).
#
# Each project gets a named gcloud configuration that remembers its account, project, region and
# zone, so one switch changes all four. Configurations live in ~/.config/gcloud and persist in
# Cloud Shell and on a laptop.
#
#   switch.sh                                    list profiles; * marks the active one
#   switch.sh c2o                                switch to the profile "c2o"
#   switch.sh add c2o admin@c2o.live c2o-live-prod [region] [zone]
#                                                create or update a profile (signs in if needed)
#   switch.sh remove NAME                        delete a profile
#
# Region and zone default to Toronto (northamerica-northeast2 / -a).
# Tip: alias gp='bash ~/C2O/deploy/gcp/switch.sh'   (add to ~/.bashrc or ~/.zshrc)

set -euo pipefail

die() { echo "switch.sh: $*" >&2; exit 1; }
command -v gcloud >/dev/null || die "gcloud is not installed"

exists() { gcloud config configurations describe "$1" >/dev/null 2>&1; }

show() {
  gcloud config configurations list \
    --format='table(is_active.yesno(yes="*",no=""):label="",name:label=PROFILE,properties.core.account:label=ACCOUNT,properties.core.project:label=PROJECT,properties.compute.region:label=REGION)'
}

case "${1:-}" in
  ""|list|status)
    show
    ;;

  add)
    [[ $# -ge 4 ]] || die "usage: switch.sh add NAME ACCOUNT PROJECT [REGION] [ZONE]"
    name=$2 account=$3 project=$4
    region=${5:-northamerica-northeast2}
    zone=${6:-${region}-a}
    [[ $name =~ ^[a-z][-a-z0-9]*$ ]] || die "profile names are lowercase letters, digits and dashes"
    if exists "$name"; then
      gcloud config configurations activate "$name" --quiet
    else
      gcloud config configurations create "$name" --quiet
    fi
    gcloud config set core/account "$account" --quiet
    gcloud config set core/project "$project" --quiet
    gcloud config set compute/region "$region" --quiet
    gcloud config set compute/zone "$zone" --quiet
    if ! gcloud auth list --format='value(account)' | grep -qx "$account"; then
      echo "No saved sign-in for $account; signing in now."
      gcloud auth login "$account"
    fi
    echo
    show
    ;;

  remove|rm)
    [[ $# -eq 2 ]] || die "usage: switch.sh remove NAME"
    gcloud config configurations delete "$2"
    ;;

  -h|--help|help)
    sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'
    ;;

  *)
    name=$1
    exists "$name" || die "no profile \"$name\". Create it with: switch.sh add $name ACCOUNT PROJECT"
    gcloud config configurations activate "$name" --quiet
    acct=$(gcloud config get-value core/account 2>/dev/null)
    proj=$(gcloud config get-value core/project 2>/dev/null)
    echo "Now on profile \"$name\": $acct · project $proj"
    if ! gcloud auth list --format='value(account)' | grep -qx "$acct"; then
      echo "No saved sign-in for $acct here. Run: gcloud auth login $acct"
    fi
    ;;
esac
