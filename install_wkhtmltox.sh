#!/bin/bash

VERSION=$1
DEBIAN_RELEASE=$2
ARCHITECTURE=$3

function fatal() {
  >&2 echo "$1"
  exit 1
}

if [ -z "$VERSION" ]; then
  fatal "wkhtmltox version to install must be passed as an argument"
fi

if [ -z "$DEBIAN_RELEASE" ]; then
  fatal "Debian release (e.g. buster) must be passed as an argument"
fi

if [ -z "$ARCHITECTURE" ]; then
  fatal "Platform architecture must be passed as an argument"
fi

if [ "386" == "$ARCHITECTURE" ]; then
  ARCHITECTURE="i386"
fi

URL="https://github.com/wkhtmltopdf/packaging/releases/download/${VERSION}/wkhtmltox_${VERSION}.${DEBIAN_RELEASE}_${ARCHITECTURE}.deb"

apt-get update || fatal "apt update failed"
apt-get -y install wget || fatal "wget install failed"
wget $URL --output-document=wkhtmltox.deb || fatal "Download of wkhtmltox failed ($URL)"
apt-get install -y ./wkhtmltox.deb || fatal "Install of wkhtmltox failed"
rm -rf /var/lib/apt/lists/* || fatal "Cleanup of apt directories failed"
rm wkhtmltox.deb || fatal "Cleanup of package download failed"
