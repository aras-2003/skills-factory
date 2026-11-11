FROM ghcr.io/marp-team/marp-cli:v4.5.1@sha256:3cf660df7b9737f875e57f7169dff0b08d1d3ab604ea2d655ab761102942fa42
USER root
# Debian APT authenticates signed Release files; HTTP avoids requiring a CA bundle in the minimal upstream image.
RUN set -eux; \
  rm -f /etc/apt/sources.list.d/*; \
  printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/%s bookworm main\n' "20261109T000000Z" > /etc/apt/sources.list; \
  printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/%s bookworm-updates main\n' "20261109T000000Z" >> /etc/apt/sources.list; \
  printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/%s bookworm-security main\n' "20261109T000000Z" >> /etc/apt/sources.list; \
  apt-get -o Acquire::Check-Valid-Until=false update; \
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    libreoffice-impress=4:7.4.7-1+deb12u14 \
    poppler-utils imagemagick fontconfig fonts-liberation libdbus-glib-1-2 curl xz-utils tesseract-ocr=5.3.0-2 tesseract-ocr-eng=1:4.1.0-2 python3=3.11.2-1+b1 weasyprint=57.2-1; \
  rm -rf /var/lib/apt/lists/*; \
  fc-cache -f; \
  set +x; \
  if ! curl -fsSL --retry 3 --output /tmp/firefox-150.0.2.tar.xz https://releases.mozilla.org/pub/firefox/releases/150.0.2/linux-x86_64/en-US/firefox-150.0.2.tar.xz >/dev/null 2>&1; then echo FIREFOX_DOWNLOAD_FAILED; exit 1; fi; \
  firefox_hash=$(sha256sum /tmp/firefox-150.0.2.tar.xz | cut -d' ' -f1); \
  if [ "$firefox_hash" != b0cda724cf29ce6775bbf28cdc032fc81225fd02f46ffec897f3768df5872241 ]; then echo FIREFOX_CHECKSUM_MISMATCH; exit 1; fi; \
  mkdir -p /opt/firefox; \
  if ! tar -xJf /tmp/firefox-150.0.2.tar.xz -C /opt/firefox >/dev/null 2>&1; then echo FIREFOX_ARCHIVE_EXTRACTION_FAILED; exit 1; fi; \
  rm -f /tmp/firefox-150.0.2.tar.xz; \
  set -x; \
  test -x /opt/firefox/firefox/firefox
COPY docker/entrypoint.sh /usr/local/bin/sf-renderer
COPY docker/inspect-pptx.py /usr/local/bin/sf-inspect-pptx
COPY docker/inspect-html.cjs /usr/local/bin/sf-inspect-html.cjs
COPY docker/inspect-pdf.py /usr/local/bin/sf-inspect-pdf.py
COPY docker/render-pdf.py /usr/local/bin/sf-render-pdf.py
COPY docker/reopen-pptx.sh /usr/local/bin/sf-reopen-pptx.sh
COPY docker/compare-images.py /usr/local/bin/sf-compare-images.py
COPY docker/font-fallback.sh /usr/local/bin/sf-font-fallback.sh
RUN chmod 0555 /usr/local/bin/sf-renderer /usr/local/bin/sf-inspect-pptx /usr/local/bin/sf-inspect-html.cjs /usr/local/bin/sf-inspect-pdf.py /usr/local/bin/sf-render-pdf.py /usr/local/bin/sf-reopen-pptx.sh /usr/local/bin/sf-compare-images.py /usr/local/bin/sf-font-fallback.sh
ENV CHROME_PATH=/usr/local/bin/chrome FIREFOX_PATH=/opt/firefox/firefox/firefox CHROME_CONFIG_HOME=/tmp/marp-config XDG_CONFIG_HOME=/tmp/.chromium-config XDG_CACHE_HOME=/tmp/.chromium-cache
ENTRYPOINT ["/usr/local/bin/sf-renderer"]
