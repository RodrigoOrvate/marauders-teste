import sys
import os
import re
import glob
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QSpinBox, 
                             QCheckBox, QPushButton, QTextEdit, QMessageBox, 
                             QTabWidget, QGroupBox, QRadioButton, QComboBox, QFormLayout, QFileDialog)
from PyQt6.QtCore import QProcess, Qt

class MaraudersApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Marauders GenoMap 🧬")
        self.resize(1200, 950)
        
        self.total_threads = os.cpu_count() or 4
        try:
            mem = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
            self.total_ram = int(mem / (1024**3))
        except: self.total_ram = 16
        
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- ABA 1: DOWNLOAD (Azul) ---
        self.tab_dl = QWidget()
        dl_lay = QVBoxLayout(self.tab_dl)
        dl_lay.addWidget(QLabel("🆔 ID do SRA (Accession):"))
        self.sra_in = QLineEdit(); self.sra_in.setMinimumHeight(40); dl_lay.addWidget(self.sra_in)

        m_box = QGroupBox("Configuração de Dados"); m_lay = QVBoxLayout()
        m_lay.addWidget(QLabel("Tipo de amostra:"))
        self.combo_type = QComboBox()
        self.combo_type.clear()
        self.combo_type.addItems([
            "Genômica (WGS / Isolados)",         # Index 0
            "Metagenômica",                      # Index 1
            "Transcriptômica (RNA-Seq)",         # Index 2
            "Metatranscriptômica (Amostras)"     # Index 3
        ])
        self.combo_type.currentIndexChanged.connect(self.sync_assembly_ui); m_lay.addWidget(self.combo_type)

        self.lay_w = QWidget(); l_lay = QVBoxLayout(self.lay_w); l_lay.addWidget(QLabel("Layout:")); self.combo_layout = QComboBox()
        self.combo_layout.addItems(["Paired-End (R1 + R2)", "Single-End (R1)"]); l_lay.addWidget(self.combo_layout); m_lay.addWidget(self.lay_w); self.lay_w.hide()
        m_box.setLayout(m_lay); dl_lay.addWidget(m_box); dl_lay.addStretch()
        
        btn_dl_lay = QHBoxLayout()
        self.btn_dl = QPushButton("🛰️  1. Baixar Dados")
        self.btn_dl.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; height: 60px; border-radius: 10px;")
        self.btn_dl.clicked.connect(self.run_dl)
        self.btn_abort = QPushButton("🛑 Abortar"); self.btn_abort.setEnabled(False)
        self.btn_abort.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold; height: 60px; border-radius: 10px;")
        self.btn_abort.clicked.connect(self.abort_process)
        btn_dl_lay.addWidget(self.btn_dl, 3); btn_dl_lay.addWidget(self.btn_abort, 1); dl_lay.addLayout(btn_dl_lay)
        self.tabs.addTab(self.tab_dl, "1. Download")

        # --- ABA 2: ASSEMBLY (Verde) ---
        self.tab_asm = QWidget(); asm_lay = QVBoxLayout(self.tab_asm)
        self.info_lab = QLabel("💡 Dica: Para genomas isolados, use MEGAHIT ou SPAdes."); self.info_lab.setStyleSheet("background: #e1f5fe; color: #01579b; padding: 12px; border-radius: 5px; font-weight: bold; border: 1px solid #b3e5fc;")
        asm_lay.addWidget(self.info_lab)

        self.group_alg = QGroupBox("Algoritmos Disponíveis"); g_lay = QVBoxLayout()
        
        descs = [
            ("MEGAHIT", "<b>MEGAHIT:</b> Projetado para lidar com grandes volumes de dados de forma extremamente eficiente. Ele utiliza uma estrutura matemática que economiza muita memória RAM, sendo a escolha obrigatória para a Metagenômica. Quando você tem uma amostra complexa, como solo ou água, onde existem milhares de espécies misturadas, o MEGAHIT consegue organizar esse caos rapidamente sem travar o computador. Ele é ideal para quem busca resultados ágeis ou possui hardware limitado, sendo muito recomendado também para genômica geral pela sua versatilidade. Além de não gerar muitos chimeras (misturas dos genomas na amostra)."),
            ("SPAdes", "<b>SPADES:</b> Ao contrário do MEGAHIT, ele não prioriza a velocidade, mas sim a precisão absoluta e a continuidade das sequências. Ele é o 'padrão ouro' para a Genômica de Isolados (WGS), ou seja, quando você está sequenciando uma única bactéria ou organismo puro no laboratório. O SPAdes tenta espremer cada detalhe das informações para entregar um genoma sem buracos, mas essa perfeição tem um custo: ele consome muita memória RAM e processamento. Por isso, ele é geralmente desabilitado para metagenomas complexos no programa, pois a quantidade de dados travaria a maioria dos servidores."),
            ("Trinity", "<b>TRINITY:</b> Focado exclusivamente em Transcriptômica e Metatranscriptômica. Enquanto os outros montadores trabalham com o DNA (o arquivo fixo), o Trinity trabalha com o RNA, que são as instruções sendo lidas pela célula naquele exato momento. Ele é mestre em identificar diferentes versões de um mesmo gene, reconstruindo os transcritos para que o pesquisador saiba exatamente o que estava 'ligado' ou 'desligado' na amostra. É uma ferramenta robusta e essencial para estudos de expressão gênica, embora também exija uma configuração de hardware cuidadosa.")
        ]

        for alg, desc in descs:
            h = QHBoxLayout(); rb = QRadioButton(alg)
            if alg == "MEGAHIT": self.radio_mega = rb; rb.setChecked(True)
            elif alg == "SPAdes": self.radio_spa = rb
            else: self.radio_trinity = rb
            lbl_h = QLabel("❓"); lbl_h.setCursor(Qt.CursorShape.WhatsThisCursor); lbl_h.setStyleSheet("color: #2980b9; font-weight: bold;")
            lbl_h.setToolTip(desc); h.addWidget(rb); h.addStretch(); h.addWidget(lbl_h); g_lay.addLayout(h)

        self.group_alg.setLayout(g_lay); asm_lay.addWidget(self.group_alg)
        
        hw_box = QGroupBox("Hardware"); hw_lay = QFormLayout()
        self.spin_t = QSpinBox(); self.spin_t.setRange(2, self.total_threads); self.spin_t.setValue(max(2, int(self.total_threads*0.7)))
        self.spin_r = QSpinBox(); self.spin_r.setRange(4, self.total_ram); self.spin_r.setValue(max(4, int(self.total_ram*0.7)))
        self.hw_advice_lab = QLabel("📊 Razão: 0 GB/Thread"); hw_lay.addRow("Threads:", self.spin_t); hw_lay.addRow("RAM (GB):", self.spin_r); hw_lay.addRow(self.hw_advice_lab)
        hw_box.setLayout(hw_lay); asm_lay.addWidget(hw_box)
        self.spin_t.valueChanged.connect(self.update_hardware_advice); self.spin_r.valueChanged.connect(self.update_hardware_advice)

        self.c_raw = QCheckBox("🧹 Excluir arquivos brutos ao finalizar"); self.c_trim = QCheckBox("🗑️ Excluir pasta de trimming ao finalizar")
        asm_lay.addWidget(self.c_raw); asm_lay.addWidget(self.c_trim); asm_lay.addStretch()
        self.btn_asm = QPushButton("🚀 Iniciar Pipeline"); self.btn_asm.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; height: 60px; border-radius: 10px;")
        self.btn_asm.clicked.connect(self.run_asm); asm_lay.addWidget(self.btn_asm)
        self.tabs.addTab(self.tab_asm, "2. Assembly")

        # --- ABA 3: PROTEIN SEARCH (Roxo) ---
        self.tab_ps = QWidget(); ps_lay = QVBoxLayout(self.tab_ps)
        ps_lay.addWidget(QLabel("🧬 Perfil HMM (.hmm):"))
        self.path_hmm = QLineEdit(); btn_h = QPushButton("Selecionar"); btn_h.clicked.connect(lambda: self.select_file(self.path_hmm))
        h2 = QHBoxLayout(); h2.addWidget(self.path_hmm); h2.addWidget(btn_h); ps_lay.addLayout(h2)
        l_pf = QLabel('<a href="https://www.ebi.ac.uk/interpro/entry/pfam/">🔗 Link Pfam para arquivos .hmm</a>')
        l_pf.setOpenExternalLinks(True); ps_lay.addWidget(l_pf); ps_lay.addStretch()
        self.btn_ps = QPushButton("🔍 Iniciar ProtSearch (Automático)"); self.btn_ps.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold; height: 50px; border-radius: 8px;")
        self.btn_ps.clicked.connect(self.run_ps); ps_lay.addWidget(self.btn_ps)
        self.tabs.addTab(self.tab_ps, "3. Protein Search")

        # --- ABA 4: GET RESULTS (Ciano) ---
        self.tab_res = QWidget(); res_lay = QVBoxLayout(self.tab_res)
        res_lay.addWidget(QLabel("📥 Esta aba coletará automaticamente os resultados HMMER (.tbl) e Proteínas (.faa) dentro da pasta do SRA."))
        res_lay.addStretch()
        self.btn_res = QPushButton("📥 Extrair Sequências (Automático)"); self.btn_res.setStyleSheet("background-color: #16a085; color: white; font-weight: bold; height: 50px; border-radius: 8px;")
        self.btn_res.clicked.connect(self.run_get_res); res_lay.addWidget(self.btn_res)
        self.tabs.addTab(self.tab_res, "4. Get Results")

        self.log = QTextEdit(); self.log.setReadOnly(True);
        self.log.document().setMaximumBlockCount(1000) # Mantém apenas as últimas 1000 linhas 
        self.log.setStyleSheet("background: black; color: #00FF00; font-family: monospace;"); main_layout.addWidget(self.log)
        self.update_hardware_advice()

    def update_hardware_advice(self):
        ratio = self.spin_r.value() / self.spin_t.value()
        status = f"📊 Razão: {ratio:.1f} GB/Thread."
        if ratio < 4.0:
            self.hw_advice_lab.setText(f"{status} ⚠️ Abaixo de 4GB/thread: Risco no Assembly.")
            self.hw_advice_lab.setStyleSheet("color: #e67e22; font-weight: bold;")
        else:
            self.hw_advice_lab.setText(f"{status} ✅ Razão segura (4GB+).")
            self.hw_advice_lab.setStyleSheet("color: #27ae60;")

    def sync_assembly_ui(self, i):
        # A caixa de Paired/Single aparece apenas para RNA-Seq (Indices 2 e 3)
        self.lay_w.setVisible(i >= 2)
        
        # Reset de algoritmos
        self.radio_mega.setEnabled(True)
        self.radio_spa.setEnabled(i == 0) # SPAdes apenas para Genômica de Isolados
        self.radio_trinity.setEnabled(i >= 2) # Trinity para os dois tipos de RNA
        
        if i == 0: # GENÔMICA
            self.info_lab.setText("💡 Recomendação: MEGAHIT para rapidez ou SPAdes para isolados puros.")
            self.radio_mega.setChecked(True)
        elif i == 1: # METAGENÔMICA
            self.info_lab.setText("💡 Recomendação: MEGAHIT é obrigatório para metagenomas complexos.")
            self.radio_mega.setChecked(True)
        elif i == 2: # TRANSCRIPTÔMICA
            self.info_lab.setText("💡 Recomendação: Trinity é o montador ideal para Transcritos (RNA-Seq).")
            self.radio_trinity.setChecked(True)
        elif i == 3: # METATRANSCRIPTÔMICA
            self.info_lab.setText("💡 Recomendação: Trinity reconstrói transcritos, mas MEGAHIT pode ser usado para comunidades.")
            self.radio_trinity.setChecked(True)

    def run_dl(self):
        sid = self.sra_in.text().strip()
        if not sid: return
        lay = "paired" if (self.combo_type.currentIndex() != 2 or self.combo_layout.currentIndex() == 0) else "single"
        self.execute_proc("bash", ["scripts/SRAget.sh", sid, lay])

    def run_asm(self):
        sid = self.sra_in.text().strip()
        if not sid: return
        asm = "trinity" if self.radio_trinity.isChecked() else ("megahit" if self.radio_mega.isChecked() else "spades")
        is_p = (self.combo_layout.currentIndex() == 0 if self.combo_type.currentIndex() == 2 else True)
        r1 = f"{sid}_1.fastq.gz" if is_p else f"{sid}.fastq.gz"
        r2 = f"{sid}_2.fastq.gz" if is_p else "none"
        args = [r1, r2, str(self.spin_t.value()), str(self.spin_r.value()), asm, "s" if self.c_raw.isChecked() else "n", "s" if self.c_trim.isChecked() else "n"]
        self.execute_proc("bash", [os.path.abspath("scripts/run_assembly.sh")] + args, os.path.abspath(sid))

    # No método run_ps do seu marauders_gui.py:

    def run_ps(self):
        sid = self.sra_in.text().strip()
        hmm = self.path_hmm.text()
        if not sid or not hmm: 
            QMessageBox.warning(self, "Erro", "Informe o ID do SRA e o arquivo HMM.")
            return
        
        mode = "meta" if self.combo_type.currentIndex() in [1, 3] else "single"
        asm_path = os.path.join(sid, "05_Assembly_Results")
        
        # --- LÓGICA DE DETECÇÃO AUTOMÁTICA DE CONTIGS ---
        contigs_file = None
        
        if self.radio_mega.isChecked():
            # MEGAHIT: final.contigs.fa dentro da subpasta MEGAHIT_*
            search = glob.glob(f"{asm_path}/MEGAHIT_*/final.contigs.fa")
            if search: contigs_file = search[0]
            
        elif self.radio_spa.isChecked():
            # SPAdes: scaffolds.fasta ou contigs.fasta na pasta SPADES_*
            # Priorizamos scaffolds por serem mais completos
            search = glob.glob(f"{asm_path}/SPADES_*/scaffolds.fasta")
            if not search:
                search = glob.glob(f"{asm_path}/SPADES_*/contigs.fasta")
            if search: contigs_file = search[0]
            
        elif self.radio_trinity.isChecked():
            # Trinity: *.Trinity.fasta na pasta TRINITY_*
            search = glob.glob(f"{asm_path}/*.Trinity.fasta")
            if search: contigs_file = search[0]

        # --- VALIDAÇÃO E EXECUÇÃO ---
        if not contigs_file or not os.path.exists(contigs_file):
            QMessageBox.warning(self, "Erro", "Arquivo de contigs não encontrado para o montador selecionado.")
            return

        self.log.append(f">>> [INFO] Contigs detectados: {os.path.basename(contigs_file)}")
        
        self.execute_proc("bash", [
            os.path.abspath("scripts/ProtSearch.sh"), 
            os.path.abspath(contigs_file), 
            os.path.abspath(hmm),
            mode
        ], os.path.abspath(sid))
        
    def run_get_res(self):
        sid = self.sra_in.text().strip()
        if not sid: return
        
        # Busca automática da tabela .tbl e das proteínas .faa
        tbls = glob.glob(f"{sid}/02_HMMER_Results/*.tbl")
        faa = f"{sid}/01_Predicted_Proteins/predicted_proteins.faa"
        
        if not tbls or not os.path.exists(faa):
            QMessageBox.warning(self, "Erro", "Resultados HMMER ou proteínas preditas não encontrados."); return
        
        self.execute_proc("bash", [os.path.abspath("scripts/get_Seq_results.sh"), os.path.abspath(tbls[0]), os.path.abspath(faa)], os.path.abspath(sid))

    def execute_proc(self, cmd, args, wd=None):
        self.set_ui_busy(True); self.proc = QProcess()
        if wd: self.proc.setWorkingDirectory(wd)
        self.proc.readyReadStandardOutput.connect(self.update_log); self.proc.readyReadStandardError.connect(self.update_log)
        self.proc.finished.connect(lambda: self.set_ui_busy(False)); self.proc.start(cmd, args)

    def select_file(self, le):
        f, _ = QFileDialog.getOpenFileName(self, "Selecionar"); (le.setText(f) if f else None)

    def set_ui_busy(self, b):
        self.btn_dl.setEnabled(not b); self.btn_asm.setEnabled(not b); self.btn_ps.setEnabled(not b); self.btn_res.setEnabled(not b); self.btn_abort.setEnabled(b)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor if b else Qt.CursorShape.ArrowCursor)

    def update_log(self):
        # Lê a saída de forma segura
        out = self.proc.readAllStandardOutput().data().decode(errors='ignore')
        err = self.proc.readAllStandardError().data().decode(errors='ignore')
        clean = (out + err).replace('\r', '\n')
        
        if clean.strip():
            # Move o cursor para o final antes de inserir
            cursor = self.log.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.log.setTextCursor(cursor)
            self.log.insertPlainText(clean)
            self.log.ensureCursorVisible()

    def abort_process(self):
        if hasattr(self, 'proc'): self.proc.kill(); self.set_ui_busy(False)

if __name__ == "__main__":
    app = QApplication(sys.argv); w = MaraudersApp(); w.show(); sys.exit(app.exec())
