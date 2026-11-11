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
    libreoffice-impress=4:7.4.7-1+deb12u14 firefox-esr=153.6.0esr-1~deb12u2 \
    poppler-utils imagemagick fontconfig fonts-liberation tesseract-ocr=5.3.0-2 tesseract-ocr-eng=1:4.1.0-2 python3=3.11.2-1+b1 weasyprint=57.2-1; \
  rm -rf /var/lib/apt/lists/*; \
  fc-cache -f; \
  set +x; \
  headless_shell=$(find /usr/local/bin/pw-browsers -type f -executable \( -name headless_shell -o -name chrome-headless-shell \) -print -quit 2>/dev/null); \
  if [ -z "$headless_shell" ]; then echo HEADLESS_SHELL_MISSING; exit 1; fi; \
  if ! ln -s "$headless_shell" /usr/local/bin/chrome-headless-shell >/dev/null 2>&1; then echo HEADLESS_SHELL_LINK_FAILED; exit 1; fi; \
  test -x /usr/local/bin/chrome-headless-shell; \
  set -x
COPY docker/entrypoint.sh /usr/local/bin/sf-renderer
COPY docker/inspect-pptx.py /usr/local/bin/sf-inspect-pptx
COPY docker/inspect-html.cjs /usr/local/bin/sf-inspect-html.cjs
COPY docker/inspect-pdf.py /usr/local/bin/sf-inspect-pdf.py
COPY docker/render-pdf.py /usr/local/bin/sf-render-pdf.py
COPY docker/reopen-pptx.sh /usr/local/bin/sf-reopen-pptx.sh
COPY docker/compare-images.py /usr/local/bin/sf-compare-images.py
COPY docker/font-fallback.sh /usr/local/bin/sf-font-fallback.sh
RUN chmod 0555 /usr/local/bin/sf-renderer /usr/local/bin/sf-inspect-pptx /usr/local/bin/sf-inspect-html.cjs /usr/local/bin/sf-inspect-pdf.py /usr/local/bin/sf-render-pdf.py /usr/local/bin/sf-reopen-pptx.sh /usr/local/bin/sf-compare-images.py /usr/local/bin/sf-font-fallback.sh
ENV CHROME_PATH=/usr/local/bin/chrome-headless-shell FIREFOX_PATH=/usr/bin/firefox-esr PUPPETEER_HEADLESS_MODE=old CHROME_CONFIG_HOME=/tmp/marp-config XDG_CONFIG_HOME=/tmp/.chromium-config XDG_CACHE_HOME=/tmp/.chromium-cache
ENTRYPOINT ["/usr/local/bin/sf-renderer"]
