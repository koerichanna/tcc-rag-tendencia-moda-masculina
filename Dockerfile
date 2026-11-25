FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV CHROMA_PERSIST_DIRECTORY=/app/data/chroma_db

WORKDIR /app

# curl para o HEALTHCHECK; sem compilador, porque só entram pacotes já compilados (wheels)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Versões e hashes travados (requirements.lock), sem rodar script de instalação de terceiros
COPY requirements.lock .
RUN pip install --no-cache-dir --require-hashes --only-binary :all: -r requirements.lock

# Modelo de embedding multilíngue (ONNX quantizado, ~135 MB) já dentro da imagem: a API sobe sem
# depender do Hugging Face e o download fica em cache entre builds enquanto requirements não muda.
ENV EMBEDDING_DIR=/app/modelos/multilingue
RUN for arquivo in tokenizer.json onnx/model_quantized.onnx; do \
      python -c "import sys; from huggingface_hub import hf_hub_download; \
hf_hub_download('Xenova/paraphrase-multilingual-MiniLM-L12-v2', sys.argv[1], local_dir='/app/modelos/multilingue')" "$arquivo"; \
    done

# Só o que a API usa (código, migrations e a base de tendências); nada de .env, testes ou dados brutos.
COPY *.py alembic.ini ./
COPY migrations/ migrations/
COPY data/market_trends.json data/

# A API roda com um usuário sem privilégios, que só escreve na base vetorial. O deploy.sh ajusta o
# dono do volume chroma_data, criado quando a imagem ainda rodava como root.
RUN useradd --create-home --uid 1000 app && mkdir -p /app/data/chroma_db && chown -R app:app /app/data
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# aplica as migrations pendentes antes de subir a API.
# --proxy-headers: usa o IP do visitante (X-Forwarded-For) em vez do IP do Nginx; a API só é
# acessível pela rede interna do Docker, então confiar no cabeçalho é seguro.
CMD ["sh", "-c", "python migrar.py && exec uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips=*"]
