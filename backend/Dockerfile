FROM verapdf/cli:v1.30.2 AS verapdf

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends default-jre-headless fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY --from=verapdf /opt/verapdf /opt/verapdf
ENV PATH="/opt/verapdf:${PATH}"
ENV VERAPDF_BIN=/opt/verapdf/verapdf

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
