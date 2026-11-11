FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV CHROMA_PERSIST_DIRECTORY=/app/data/chroma_db

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Modelo de embedding multilíngue (ONNX quantizado, ~135 MB) já dentro da imagem: a API sobe sem
# depender do Hugging Face e o download fica em cache entre builds enquanto requirements não muda.
ENV EMBEDDING_DIR=/app/modelos/multilingue
RUN for arquivo in tokenizer.json onnx/model_quantized.onnx; do \
      python -c "import sys; from huggingface_hub import hf_hub_download; \
hf_hub_download('Xenova/paraphrase-multilingual-MiniLM-L12-v2', sys.argv[1], local_dir='/app/modelos/multilingue')" "$arquivo"; \
    done

COPY . .

RUN mkdir -p /app/data/chroma_db

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# aplica as migrations pendentes antes de subir a API.
# --proxy-headers: usa o IP do visitante (X-Forwarded-For) em vez do IP do Nginx; a API só é
# acessível pela rede interna do Docker, então confiar no cabeçalho é seguro.
CMD ["sh", "-c", "python migrar.py && exec uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips=*"]
