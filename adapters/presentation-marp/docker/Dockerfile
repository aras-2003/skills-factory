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
    poppler-utils imagemagick fontconfig fonts-liberation libdbus-glib-1-2 tesseract-ocr=5.3.0-2 tesseract-ocr-eng=1:4.1.0-2 python3=3.11.2-1+b1 weasyprint=57.2-1; \
  rm -rf /var/lib/apt/lists/*; \
  fc-cache -f; \
  node /home/marp/.cli/node_modules/@puppeteer/browsers/lib/cjs/main-cli.js install firefox@150.0.2 --path /opt/puppeteer-browsers; \
  test -x /opt/puppeteer-browsers/firefox/linux-150.0.2/firefox/firefox
COPY docker/entrypoint.sh /usr/local/bin/sf-renderer
COPY docker/inspect-pptx.py /usr/local/bin/sf-inspect-pptx
COPY docker/inspect-html.cjs /usr/local/bin/sf-inspect-html.cjs
COPY docker/inspect-pdf.py /usr/local/bin/sf-inspect-pdf.py
COPY docker/render-pdf.py /usr/local/bin/sf-render-pdf.py
COPY docker/reopen-pptx.sh /usr/local/bin/sf-reopen-pptx.sh
COPY docker/compare-images.py /usr/local/bin/sf-compare-images.py
COPY docker/font-fallback.sh /usr/local/bin/sf-font-fallback.sh
RUN chmod 0555 /usr/local/bin/sf-renderer /usr/local/bin/sf-inspect-pptx /usr/local/bin/sf-inspect-html.cjs /usr/local/bin/sf-inspect-pdf.py /usr/local/bin/sf-render-pdf.py /usr/local/bin/sf-reopen-pptx.sh /usr/local/bin/sf-compare-images.py /usr/local/bin/sf-font-fallback.sh
ENV CHROME_PATH=/usr/local/bin/chrome FIREFOX_PATH=/opt/puppeteer-browsers/firefox/linux-150.0.2/firefox/firefox CHROME_CONFIG_HOME=/tmp/marp-config XDG_CONFIG_HOME=/tmp/.chromium-config XDG_CACHE_HOME=/tmp/.chromium-cache
ENTRYPOINT ["/usr/local/bin/sf-renderer"]
