FROM python:3.12-slim
LABEL org.opencontainers.image.source="https://github.com/heinrihs-s/dots-on-paper"
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .
ENV DOTS_HOST=0.0.0.0 DOTS_PORT=9035 DOTS_DATA_DIR=/data DOTS_CONFIG_FILE=/data/credentials.json
RUN useradd --uid 10001 --create-home bridge && mkdir /data && chown bridge:bridge /data
USER bridge
EXPOSE 9035
CMD ["python", "-m", "dots_on_paper"]
