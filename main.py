"""NEMESIS Tutor — desktop tutor for authorized cybersecurity learning.

The application offers a floating orb, an NVIDIA API chat, explicit screen
analysis and Markdown report generation. It does not run terminal commands.
"""
from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

from openai import OpenAI
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QSettings, Qt, QThread, QTimer, Signal, QRectF, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QFont, QGuiApplication, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout,
    QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPlainTextEdit,
    QPushButton, QStackedWidget, QTextBrowser, QVBoxLayout, QWidget,
)

APP_NAME = "NEMESIS Tutor"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_TEXT_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"
DEFAULT_VISION_MODEL = "nvidia/nemotron-3.5-super-vl-120b-a12b"
SETTINGS = QSettings("Stylesxz", "NemesisTutor")

SYSTEM_PROMPT = """Você é o NEMESIS Tutor, instrutor de cibersegurança responsável.
Responda em português brasileiro, de forma clara, direta e didática. Comece pela
resposta principal. Evite introduções longas, repetir a pergunta, jargões sem
explicação e listas extensas. Prefira parágrafos curtos. Em dúvidas simples,
responda diretamente em 1 a 4 parágrafos. Use Markdown para organizar a resposta.
Ao analisar evidências, use quando for útil:
**Resumo:** conclusão principal em uma frase.
**O que foi observado:** fatos presentes nos dados fornecidos.
**O que isso pode significar:** interpretação provável, sem afirmar o que não foi comprovado.
**O que falta confirmar:** incertezas e possíveis falsos positivos.
**Próximo passo seguro:** uma ação objetiva e autorizada.
Não precisa usar todas as seções em toda resposta. Explique comandos brevemente.
Nunca invente resultados, não afirme que executou comandos e não peça senhas,
tokens ou chaves. Oriente testes somente em laboratórios, sistemas próprios ou
alvos com autorização explícita. Não ajude com roubo/exfiltração de dados,
persistência, evasão, malware ou exploração destrutiva; priorize validação
defensiva e remediação. Avise se houver dados sensíveis visíveis.
"""

APP_STYLE = """
QWidget#root { background:#080808; color:#f0f0f0; border:1px solid #454545; border-radius:18px; }
QFrame#card { background:#0b0b0b; border:1px solid #303030; border-radius:14px; }
QLabel { color:#f1f1f1; }
QLabel#muted { color:#a3a3a3; font-size:10px; }
QLabel#brand { font-size:15px; font-weight:800; letter-spacing:2px; }
QPushButton { color:#eee; background:#202020; border:1px solid #474747; border-radius:9px; padding:8px 11px; }
QPushButton:hover { background:#333; border-color:#aaa; }
QPushButton#primary { color:#080808; background:#eee; border-color:#fff; font-weight:800; }
QPushButton#tabActive { color:#080808; background:#eee; font-weight:800; }
QLineEdit, QComboBox, QPlainTextEdit { background:#171717; color:#eee; border:1px solid #444; border-radius:10px; padding:8px; selection-background-color:#666; }
QTextBrowser { background:#090909; color:#eee; border:1px solid #333; border-radius:12px; padding:7px; }
QScrollBar:vertical { background:#111; width:7px; } QScrollBar::handle:vertical { background:#555; border-radius:3px; }
"""


class ApiWorker(QThread):
    success = Signal(str, str)
    failure = Signal(str, str)

    def __init__(self, api_key: str, model: str, messages: list, task: str, max_tokens: int = 3500):
        super().__init__()
        self.api_key, self.model, self.messages = api_key, model, messages
        self.task, self.max_tokens = task, max_tokens

    def run(self):
        try:
            client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=self.api_key, timeout=120.0, max_retries=1)
            response = client.chat.completions.create(
                model=self.model, messages=self.messages, max_tokens=self.max_tokens,
                temperature=0.7, top_p=0.95,
            )
            self.success.emit(self.task, response.choices[0].message.content or "A API retornou uma resposta vazia.")
        except Exception as exc:
            self.failure.emit(self.task, str(exc).strip() or exc.__class__.__name__)


class FloatingOrb(QWidget):
    clicked = Signal()

    def __init__(self):
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(78, 78)
        self.setToolTip("NEMESIS Tutor — clique para abrir e arraste para mover")
        self._drag_offset = None
        self._moved = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        halo = QRadialGradient(39, 39, 39)
        halo.setColorAt(0, QColor(235, 235, 235, 55))
        halo.setColorAt(0.75, QColor(150, 150, 150, 18))
        halo.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(halo)
        painter.drawEllipse(QRectF(0, 0, 78, 78))
        grad = QRadialGradient(26, 21, 55)
        grad.setColorAt(0, QColor(85, 85, 85))
        grad.setColorAt(1, QColor(5, 5, 5))
        painter.setBrush(grad)
        painter.setPen(QPen(QColor(235, 235, 235, 220), 1.7))
        painter.drawEllipse(QRectF(9, 9, 60, 60))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(15, 15, 48, 48))
        painter.setPen(QPen(QColor(255, 255, 255), 2.7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawLine(28, 49, 28, 29)
        painter.drawLine(28, 29, 50, 49)
        painter.drawLine(50, 49, 50, 29)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._moved = False

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            point = event.globalPosition().toPoint() - self._drag_offset
            if (point - self.pos()).manhattanLength() > 3:
                self._moved = True
            self.move(point)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._moved:
                self.clicked.emit()
            self._drag_offset = None


class SettingsDialog(QDialog):
    def __init__(self, parent, api_key: str, text_model: str, vision_model: str):
        super().__init__(parent)
        self.setWindowTitle("Configuração da API NVIDIA")
        self.setModal(True)
        self.setMinimumWidth(440)
        self.setStyleSheet(APP_STYLE)
        layout = QVBoxLayout(self)
        title = QLabel("Conectar ao NVIDIA NIM")
        title.setStyleSheet("font-size:18px;font-weight:800")
        layout.addWidget(title)
        layout.addWidget(QLabel("A chave fica nesta sessão, salvo se você optar pelo cofre seguro do sistema."))
        form = QFormLayout()
        self.key_field = QLineEdit(api_key)
        self.key_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_field.setPlaceholderText("nvapi-…")
        self.text_field = QComboBox()
        self.text_field.setEditable(True)
        self.text_field.addItems([DEFAULT_TEXT_MODEL, "nvidia/nemotron-3.5-lightning-30b-a3b", DEFAULT_VISION_MODEL, "moonshotai/kimi-k3"])
        self.text_field.setCurrentText(text_model)
        self.vision_field = QComboBox()
        self.vision_field.setEditable(True)
        self.vision_field.addItems([DEFAULT_VISION_MODEL, "nvidia/nemotron-3.5-lightning-30b-a3b", "moonshotai/kimi-k3"])
        self.vision_field.setCurrentText(vision_model)
        self.save_key = QCheckBox("Guardar a chave no cofre do sistema operacional")
        form.addRow("Chave da API", self.key_field)
        form.addRow("Modelo de texto", self.text_field)
        form.addRow("Modelo visual", self.vision_field)
        layout.addLayout(form)
        layout.addWidget(self.save_key)
        link = QPushButton("Abrir portal NVIDIA para obter uma chave ↗")
        link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://build.nvidia.com/")))
        layout.addWidget(link)
        buttons = QHBoxLayout()
        cancel, save = QPushButton("Cancelar"), QPushButton("Salvar")
        save.setObjectName("primary")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.accept)
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def values(self):
        return self.key_field.text().strip(), self.text_field.currentText().strip(), self.vision_field.currentText().strip(), self.save_key.isChecked()


class MainWindow(QWidget):
    hide_to_orb = Signal()

    def __init__(self):
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setObjectName("root")
        self.setWindowTitle(APP_NAME)
        self.setFixedSize(500, 730)
        self.setStyleSheet(APP_STYLE)
        self.api_key = os.environ.get("NVIDIA_API_KEY", "").strip()
        self.text_model = SETTINGS.value("text_model", DEFAULT_TEXT_MODEL)
        self.vision_model = SETTINGS.value("vision_model", DEFAULT_VISION_MODEL)
        self.history = []
        self.transcript = []
        self.busy = False
        self.worker = None
        if not self.api_key:
            self._load_saved_key()
        self._build_ui()
        self._add_message("NEMESIS", "Olá! Sou seu tutor de cibersegurança. Configure a API NVIDIA (⚙), descreva seu laboratório autorizado e envie uma pergunta ou saída para análise.")
        self._set_status()

    def _load_saved_key(self):
        try:
            import keyring
            self.api_key = keyring.get_password("NemesisTutorNVIDIA", "api_key") or ""
        except Exception:
            self.api_key = ""

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 12, 14, 14)
        header = QHBoxLayout()
        mark = QLabel("N")
        mark.setFixedSize(40, 40)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setStyleSheet("border:1px solid #aaa;border-radius:20px;font-size:21px;font-weight:800")
        brand = QVBoxLayout()
        name = QLabel("NEMESIS")
        name.setObjectName("brand")
        subtitle = QLabel("CYBERSECURITY TUTOR")
        subtitle.setObjectName("muted")
        brand.addWidget(name)
        brand.addWidget(subtitle)
        self.status = QLabel("API não configurada")
        self.status.setObjectName("muted")
        settings = QPushButton("⚙")
        settings.clicked.connect(self.configure)
        close = QPushButton("×")
        close.clicked.connect(self._hide)
        header.addWidget(mark)
        header.addLayout(brand, 1)
        header.addWidget(self.status)
        header.addWidget(settings)
        header.addWidget(close)
        outer.addLayout(header)
        tabs = QHBoxLayout()
        self.chat_tab, self.report_tab = QPushButton("TUTOR"), QPushButton("RELATÓRIO")
        self.chat_tab.setObjectName("tabActive")
        self.chat_tab.clicked.connect(lambda: self._show_page(0))
        self.report_tab.clicked.connect(lambda: self._show_page(1))
        tabs.addWidget(self.chat_tab)
        tabs.addWidget(self.report_tab)
        outer.addLayout(tabs)
        self.pages = QStackedWidget()
        self.pages.addWidget(self._chat_page())
        self.pages.addWidget(self._report_page())
        outer.addWidget(self.pages, 1)

    def _chat_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        intro = QFrame()
        intro.setObjectName("card")
        intro_l = QVBoxLayout(intro)
        title = QLabel("Seu copiloto de laboratório")
        title.setStyleSheet("font-size:16px;font-weight:800")
        intro_l.addWidget(title)
        intro_l.addWidget(QLabel("Interprete saídas, valide hipóteses e aprenda o próximo passo."))
        layout.addWidget(intro)
        self.chat = QTextBrowser()
        self.chat.setOpenExternalLinks(True)
        layout.addWidget(self.chat, 1)
        self.input = QPlainTextEdit()
        self.input.setPlaceholderText("Pergunte sobre um comando, resultado ou conceito…")
        self.input.setFixedHeight(78)
        layout.addWidget(self.input)
        row = QHBoxLayout()
        self.screen_button = QPushButton("◎ Analisar tela")
        self.screen_button.clicked.connect(self.analyze_screen)
        self.send_button = QPushButton("Enviar ↑")
        self.send_button.setObjectName("primary")
        self.send_button.clicked.connect(self.send_chat)
        row.addWidget(self.screen_button)
        row.addStretch(1)
        row.addWidget(self.send_button)
        layout.addLayout(row)
        tip = QLabel("Captura somente ao clicar · envio explícito à NVIDIA · sem execução de comandos")
        tip.setObjectName("muted")
        layout.addWidget(tip)
        return page

    def _report_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Relatório de pentest"))
        self.scope = QPlainTextEdit()
        self.scope.setPlaceholderText("Escopo autorizado, ativo, objetivo e limitações…")
        self.scope.setFixedHeight(85)
        layout.addWidget(self.scope)
        self.evidence = QPlainTextEdit()
        self.evidence.setPlaceholderText("Cole evidências, comandos e resultados que deseja documentar…")
        layout.addWidget(self.evidence, 1)
        row = QHBoxLayout()
        self.generate_button = QPushButton("Gerar relatório")
        self.generate_button.setObjectName("primary")
        self.generate_button.clicked.connect(self.generate_report)
        self.save_button = QPushButton("Salvar .md")
        self.save_button.clicked.connect(self.save_report)
        row.addWidget(self.generate_button)
        row.addWidget(self.save_button)
        layout.addLayout(row)
        self.report_output = QTextBrowser()
        layout.addWidget(self.report_output, 1)
        return page

    def _show_page(self, index):
        self.pages.setCurrentIndex(index)
        self.chat_tab.setObjectName("tabActive" if index == 0 else "")
        self.report_tab.setObjectName("tabActive" if index == 1 else "")
        for button in (self.chat_tab, self.report_tab):
            button.style().unpolish(button)
            button.style().polish(button)

    def _set_status(self):
        self.status.setText("NVIDIA · configurada" if self.api_key else "API não configurada")

    def configure(self):
        dialog = SettingsDialog(self, self.api_key, self.text_model, self.vision_model)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        key, text_model, vision_model, save_key = dialog.values()
        if not key or not text_model or not vision_model:
            QMessageBox.warning(self, "Configuração incompleta", "Informe a chave e os dois IDs de modelo.")
            return
        self.api_key, self.text_model, self.vision_model = key, text_model, vision_model
        SETTINGS.setValue("text_model", text_model)
        SETTINGS.setValue("vision_model", vision_model)
        if save_key:
            try:
                import keyring
                keyring.set_password("NemesisTutorNVIDIA", "api_key", key)
            except Exception as exc:
                QMessageBox.warning(self, "Cofre indisponível", "A chave ficará somente nesta sessão. O cofre do sistema não está disponível.\n\n" + str(exc))
        self._set_status()

    def _add_message(self, speaker: str, text: str):
        self.transcript.append((speaker, text))
        markdown = []

        for name, message in self.transcript:
            markdown.append(f"### {name}\n\n{message}")

        # QTextBrowser renderiza Markdown (títulos, listas e blocos de código),
        # mantendo a conversa completa e deslocando a visualização ao fim.
        bar = self.chat.verticalScrollBar()
        old_value = bar.value()
        was_at_bottom = old_value >= bar.maximum() - 8
        self.chat.setMarkdown("\n\n---\n\n".join(markdown))
        if was_at_bottom or len(self.transcript) == 1:
            bar.setValue(bar.maximum())

    def _require_key(self):
        if not self.api_key:
            QMessageBox.information(self, "Configure a API", "Abra Configurações (⚙) e informe sua chave da API NVIDIA.")
            return False
        return True

    def send_chat(self):
        text = self.input.toPlainText().strip()
        if not text or self.busy or not self._require_key():
            return
        self.input.clear()
        self._add_message("VOCÊ", text)
        self.history.append({"role": "user", "content": text})
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, *self.history[-14:]]
        self._start_request(self.text_model, messages, "chat")

    def analyze_screen(self):
        if self.busy or not self._require_key():
            return
        answer = QMessageBox.question(self, "Enviar captura à NVIDIA", "A tela principal será capturada e enviada à API NVIDIA. Oculte senhas, tokens e informações privadas antes de continuar. Deseja capturar e enviar agora?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.hide()
        QTimer.singleShot(450, self._capture_and_send)

    def _capture_and_send(self):
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            self.show()
            QMessageBox.warning(self, "Captura indisponível", "Não foi possível identificar a tela principal.")
            return
        pixmap = screen.grabWindow(0)
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        pixmap.save(buffer, "PNG")
        image_data = base64.b64encode(bytes(buffer.data())).decode("ascii")
        buffer.close()
        self.show()
        self.raise_()
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": "Analise esta captura de tela. Liste fatos visíveis, interpretações prováveis, incertezas/falsos positivos, próximo passo seguro e o que documentar. Não invente detalhes ausentes."},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64," + image_data}},
            ]},
        ]
        self._start_request(self.vision_model, messages, "screen")

    def generate_report(self):
        if self.busy or not self._require_key():
            return
        prompt = "Gere um relatório preliminar em Markdown sem inventar fatos. Diferencie evidências fornecidas, hipóteses e itens ainda não validados. Inclua escopo, resumo executivo, metodologia, achados, impacto, severidade justificada, limitações e recomendações.\n\nESCOPO:\n" + self.scope.toPlainText().strip() + "\n\nEVIDÊNCIAS:\n" + self.evidence.toPlainText().strip()
        self._start_request(self.text_model, [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}], "report", 5000)
        self.report_output.setPlainText("Gerando relatório com os dados fornecidos…")

    def save_report(self):
        content = self.report_output.toPlainText().strip()
        if not content or content.startswith("Gerando relatório"):
            QMessageBox.information(self, "Nada para salvar", "Gere o relatório antes de salvar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar relatório", str(Path.home() / "relatorio-pentest-nemesis.md"), "Markdown (*.md)")
        if path:
            if not path.endswith(".md"):
                path += ".md"
            Path(path).write_text(content, encoding="utf-8")

    def _start_request(self, model, messages, task, max_tokens=3500):
        self.busy = True
        self._set_busy(True)
        self.worker = ApiWorker(self.api_key, model, messages, task, max_tokens)
        self.worker.success.connect(self._request_success)
        self.worker.failure.connect(self._request_failure)
        self.worker.start()

    def _set_busy(self, busy):
        self.busy = busy
        for button in (self.send_button, self.screen_button, self.generate_button):
            button.setEnabled(not busy)
        self.status.setText("NVIDIA · processando…" if busy else ("NVIDIA · configurada" if self.api_key else "API não configurada"))

    def _request_success(self, task, answer):
        if task in ("chat", "screen"):
            self._add_message("NEMESIS", answer)
            if task == "chat":
                self.history.append({"role": "assistant", "content": answer})
        elif task == "report":
            self.report_output.setPlainText(answer)
        self._set_busy(False)
        self.worker = None

    def _request_failure(self, task, error):
        low = error.lower()
        if "401" in low or "unauthorized" in low:
            message = "A chave NVIDIA foi recusada. Confira se ela está correta e ativa."
        elif "403" in low or "permission" in low:
            message = "Sua conta pode não ter acesso a esse modelo. Verifique a permissão no catálogo NVIDIA."
        elif "404" in low or "not found" in low:
            message = "Modelo ou endpoint não encontrado. Confira o ID configurado."
        elif "429" in low or "quota" in low or "rate limit" in low:
            message = "Limite ou cota da API atingido. Confira os limites da sua conta NVIDIA."
        else:
            message = "Falha na solicitação: " + error[:1000]
        if task in ("chat", "screen"):
            self._add_message("NEMESIS", message)
        else:
            self.report_output.setPlainText(message)
        self._set_busy(False)
        self.worker = None

    def _hide(self):
        self.hide()
        self.hide_to_orb.emit()

    def closeEvent(self, event):
        event.ignore()
        self._hide()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("Stylesxz")
    app.setQuitOnLastWindowClosed(False)
    app.setFont(QFont("Inter", 10))
    orb, window = FloatingOrb(), MainWindow()

    def toggle_window():
        if window.isVisible():
            window.hide()
            orb.show()
        else:
            orb.hide()
            window.show()
            window.raise_()
            window.activateWindow()
            screen = QGuiApplication.primaryScreen()
            if screen:
                area = screen.availableGeometry()
                window.move(area.right() - window.width() - 24, area.bottom() - window.height() - 24)

    orb.clicked.connect(toggle_window)
    window.hide_to_orb.connect(orb.show)
    screen = QGuiApplication.primaryScreen()
    if screen:
        area = screen.availableGeometry()
        orb.move(area.right() - orb.width() - 24, area.bottom() - orb.height() - 30)
    orb.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
