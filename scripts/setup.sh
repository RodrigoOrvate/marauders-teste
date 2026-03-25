#!/bin/bash
# Marauders GenoMap Setup - Versão Final de Alta Visibilidade
# Data: 25 de Março de 2026
set -e

echo "🧬 Iniciando Setup Automatizado do Marauders GenoMap..."
echo "--------------------------------------------------------"
echo "⚠️  AVISO PARA PRIMEIRA INSTALAÇÃO:"
echo "🐢 Este processo é PESADO e pode levar de 15 a 40 minutos."
echo "📦 Modo de Baixo Consumo de RAM: Instalando pacotes em blocos."
echo "☕ Busque um café; o Conda/Mamba está trabalhando para você!"
echo "--------------------------------------------------------"

## --- 1. Localização e Carregamento do Conda ---
CONDA_PATH="$HOME/miniconda"
CONDA_SH="$CONDA_PATH/etc/profile.d/conda.sh"

if [ ! -d "$CONDA_PATH" ]; then
    echo "🐍 Conda não detectado. Iniciando instalação completa..."
    
    echo "📥 Baixando instalador do Miniconda..."
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
    
    echo "⚙️  Executando instalador (isso pode levar uns minutos...)"
    bash miniconda.sh -b -p "$CONDA_PATH"
    rm miniconda.sh
    
    echo "🔧 Inicializando Conda permanentemente no sistema..."
    "$CONDA_PATH/bin/conda" init bash
    
    source "$CONDA_SH"
    echo "⚖️  Aceitando Termos de Serviço da Anaconda..."
    conda tos accept || true
else
    echo "✅ Conda já instalado em $CONDA_PATH."
    source "$CONDA_SH" || export PATH="$CONDA_PATH/bin:$PATH"
fi

# Garante que o comando conda funciona agora para o restante do script
source "$CONDA_SH"

## --- 2. Garantia do Mamba e Canais ---
if ! command -v mamba &> /dev/null; then
    echo "⚡ Instalando Mamba (Gerenciador ultra-rápido)..."
    conda install -n base -c conda-forge mamba -y || true
    source "$CONDA_SH"
fi

conda activate base
conda config --add channels conda-forge --quiet
conda config --add channels bioconda --quiet
conda config --set channel_priority flexible

## --- 3. Criação do Ambiente e Instalação ---
if ! conda info --envs | grep -q "marauders"; then
    echo "🏗️ Criando ambiente marauders..."
    mamba create -y -n marauders python=3.10
fi

conda activate marauders

# Verifica se o PyQt6 ou Spades faltam para decidir se roda a instalação pesada
if ! python3 -c "import PyQt6" 2>/dev/null || ! command -v spades.py &> /dev/null; then
    echo "📦 Instalando/Atualizando Ferramentas (Blocos)..."
    mamba install -y pigz parallel fastqc trimmomatic bbmap seqtk samtools bamtools biopython
    mamba install -y spades trinity megahit
    mamba install -y prodigal hmmer multiqc pyqt6
else
    echo "✅ Ferramentas e bibliotecas já estão em ordem. Pulando..."
fi

## --- 4. Binários NCBI ---
if ! command -v prefetch &> /dev/null; then
    echo "📥 Instalando SRA Toolkit..."
    wget -q "https://ftp-trace.ncbi.nlm.nih.gov/sra/sdk/current/sratoolkit.current-ubuntu64.tar.gz" -O sra.tar.gz
    tar -xzf sra.tar.gz && sudo cp -r sratoolkit.*/bin/* /usr/local/bin/ && rm -rf sra.tar.gz sratoolkit*
fi

## --- 5. CHECK-UP DETALHADO (Lista Completa) ---
echo -e "\n--- 📊 CHECK-UP FINAL MARAUDERS ---"
echo "🛠️  Ferramentas de Sistema:"
for t in conda mamba pigz parallel; do
    command -v "$t" &> /dev/null && echo "  ✅ [OK] $t" || echo "  ❌ [FALTA] $t"
done

echo "🧬 Bioinformática & Montadores:"
for t in prefetch fasterq-dump fastqc trimmomatic bbnorm.sh seqtk samtools megahit spades.py Trinity prodigal hmmsearch multiqc; do
    command -v "$t" &> /dev/null && echo "  ✅ [OK] $t" || echo "  ❌ [FALTA] $t"
done

echo "🐍 Bibliotecas Python (Venv):"
python3 -c "import Bio" 2>/dev/null && echo "  ✅ [OK] Biopython" || echo "  ❌ [FALTA] Biopython"
python3 -c "import PyQt6" 2>/dev/null && echo "  ✅ [OK] PyQt6" || echo "  ❌ [FALTA] PyQt6"

## --- 6. CONFIGURAÇÃO DO COMANDO GLOBAL (AUTOMAÇÃO TOTAL) ---
if [ -f "Makefile" ]; then
    PROJECT_ROOT=$(pwd)
elif [ -f "../Makefile" ]; then
    cd ..
    PROJECT_ROOT=$(pwd)
fi

if [ -n "$PROJECT_ROOT" ]; then
    echo -e "\n🛠️  Configurando comando 'marauders' em: $PROJECT_ROOT"
    
    cat <<EOF > marauders_temp
#!/bin/bash
# 1. Correção de vídeo para Ubuntu moderno
export QT_QPA_PLATFORM=xcb

# 2. Localização dinâmica do Conda para ativação automática
CONDA_SH_LOCAL="\$HOME/miniconda/etc/profile.d/conda.sh"

if [ -f "\$CONDA_SH_LOCAL" ]; then
    source "\$CONDA_SH_LOCAL"
    conda activate marauders
fi

# 3. Navega até a pasta do projeto e executa a interface
cd "$PROJECT_ROOT"
python3 marauders_gui.py
EOF
    
    chmod +x marauders_temp
    sudo mv marauders_temp /usr/local/bin/marauders
    echo "✅ Comando 'marauders' configurado com sucesso!"
fi

echo "--------------------------------------------------------"
echo "🚀 SETUP CONCLUÍDO COM SUCESSO!"
echo "💡 O ambiente é ativado automaticamente pelo comando."
echo "💡 Basta digitar: marauders"
echo "--------------------------------------------------------"
