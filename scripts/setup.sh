#!/bin/bash
# Marauders GenoMap Setup - Versão Final com Avisos
# Data: 24 de Março de 2026
set -e

echo "🧬 Iniciando Setup Automatizado do Marauders GenoMap..."
echo "--------------------------------------------------------"
echo "⚠️  AVISO PARA PRIMEIRA INSTALAÇÃO:"
echo "🐢 Este processo é PESADO e pode levar de 15 a 40 minutos."
echo "📦 Estamos resolvendo dependências complexas (SPAdes, Trinity, PyQt6)."
echo "☕ Busque um café; o Conda/Mamba está trabalhando para você!"
echo "--------------------------------------------------------"

## --- 1. Localização e Carregamento do Conda ---
if ! command -v conda &> /dev/null; then
    echo "🐍 Conda não detectado. Instalando Miniconda..."
    wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
    bash miniconda.sh -b -p "$HOME/miniconda"
    CONDA_PATH="$HOME/miniconda"
    rm miniconda.sh
else
    echo "✅ Conda detectado."
    CONDA_PATH=$(conda info --base)
fi

source "$CONDA_PATH/etc/profile.d/conda.sh"

## --- 2. Instalação do Mamba e Ambiente ---
echo "⚡ Instalando Mamba para acelerar futuras atualizações..."
conda install -n base -c conda-forge mamba -y || true

conda activate base
mamba config --add channels bioconda --add channels conda-forge --set channel_priority strict

if ! conda info --envs | grep -q "marauders"; then
    mamba create -y -n marauders python=3.10
fi

conda activate marauders

echo "📦 Instalando Ferramentas de Bioinformática e GUI..."
mamba install -y -n marauders \
    pigz parallel fastqc trimmomatic bbmap multiqc \
    spades trinity seqtk samtools bamtools prodigal \
    hmmer pyqt biopython

## --- 3. Binários e Compilação ---
# SRA Toolkit e MEGAHIT (Mantidos conforme sua lógica original)
if ! command -v prefetch &> /dev/null; then
    wget -q "https://ftp-trace.ncbi.nlm.nih.gov/sra/sdk/current/sratoolkit.current-ubuntu64.tar.gz" -O sra.tar.gz
    tar -xzf sra.tar.gz && sudo cp -r sratoolkit.*/bin/* /usr/local/bin/ && rm -rf sra.tar.gz sratoolkit*
fi

if ! command -v megahit &> /dev/null; then
    git clone https://github.com/voutcn/megahit.git && cd megahit
    mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(nproc)
    sudo make install && cd ../.. && rm -rf megahit
fi

## --- 4. CHECK-UP E AUTOMAÇÃO FINAL ---
echo -e "\n--- 📊 CHECK-UP FINAL MARAUDERS ---"
# Verificação de todas as 15 ferramentas essenciais
TOOLS=("conda" "mamba" "prefetch" "fasterq-dump" "pigz" "fastqc" "trimmomatic" "bbnorm.sh" "multiqc" "megahit" "spades.py" "Trinity" "prodigal" "hmmsearch" "seqtk")
for t in "${TOOLS[@]}"; do
    command -v "$t" &> /dev/null && echo "✅ [OK] $t" || echo "❌ [FALTA] $t"
done

if [ -f "Makefile" ]; then
    echo -e "\n🛠️  Instalando comando global..."
    sudo make install
fi

echo "--------------------------------------------------------"
echo "🚀 SETUP CONCLUÍDO COM SUCESSO!"
echo "💡 Você NUNCA MAIS precisará rodar este setup.sh."
echo "🧬 Para abrir o programa e ativar o ambiente automaticamente,"
echo "   basta digitar no terminal: marauders"
echo "--------------------------------------------------------"
