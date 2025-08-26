FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

# Build-Optimierungen (nicht applikationsspezifisch), daher nicht in .env
# Umgebungsvariablen für CUDA 12.4
ENV DEBIAN_FRONTEND=noninteractive \
    PATH=/usr/local/cuda-12.4/bin:${PATH} \
    LD_LIBRARY_PATH=/usr/local/cuda-12.4/lib64:${LD_LIBRARY_PATH}

# Abhängigkeiten installieren
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    wget \
    curl \
    git \
    ca-certificates \
    build-essential \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    libopenblas-dev \
    libopenmpi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Python 3.11 als Standard
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Symlink: python -> python3 (vermeidet Exec-Fehler)
RUN ln -sf /usr/local/bin/python3 /usr/local/bin/python


# uv installieren
RUN curl -fsSL https://astral.sh/uv/install.sh | sh \
    && mv ~/.local/bin/uv /usr/local/bin/uv

WORKDIR /app
COPY requirements.txt .

# Torch mit CUDA 12.4 installieren (extra-index-url direkt im RUN-Befehl)
# Kompatibilitätsliste: https://pytorch.org/get-started/previous-versions/
#
# ENV nicht in .env verschieben, notwendig zur Vermeidung des Abbruchs des Torch-Wheels (extra Speicher hiermit zugewiesen)
ENV TMPDIR=/var/tmp

RUN uv pip install --system --no-cache-dir \
    torch==2.4.1 --index-url https://download.pytorch.org/whl/cu124 \
    && uv pip install --system --no-cache-dir -r requirements.txt

# Rest der Anwendung kopieren
COPY . .

EXPOSE 8501 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501"]
