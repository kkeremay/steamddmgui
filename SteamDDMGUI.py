import sys
import os
import platform
import re
import zipfile
import shutil
import subprocess
import threading
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QPushButton, QLabel, QProgressBar, QFileDialog, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QThread

if platform.system() == "Windows":
    from subprocess import CREATE_NO_WINDOW
else:
    CREATE_NO_WINDOW = 0

class DownloadWorker(QObject):

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    finished = pyqtSignal(int)
    progress = pyqtSignal(float)
    status = pyqtSignal(str)

    def run_download_logic(self, target_dir, final_download_dir, base_dir, use_steamless=False, use_goldberg=True):
        lua_file = next((os.path.join(root, f) for root, _, files in os.walk(target_dir) for f in files if f.endswith('.lua')), None)
        manifest_file = next((os.path.join(root, f) for root, _, files in os.walk(target_dir) for f in files if f.endswith('.manifest')), None)

        if not lua_file or not manifest_file:
            return "Error: Missing .lua or .manifest"

        with open(lua_file, 'r') as f:
            content = f.read()

        app_id = re.search(r'addappid\((\d+)\)', content).group(1)
        depot_datas = re.findall(r'addappid\((\d+,0,"[a-fA-F0-9]+")\)', content, re.DOTALL)
        total_depots = len(depot_datas)
        for i, depot_data in enumerate(depot_datas):
            depot_id = depot_data.split(',')[0]
            key = depot_data.split('"')[1]
            manifest_id = re.search(rf'setManifestid\({depot_id},\"(\d+)\"', content).group(1)
            
            keyfile_path = os.path.join(target_dir, "temp_keys.txt")
            with open(keyfile_path, 'w') as f:
                f.write(f"{depot_id};{key}")

            if platform.system() == "Linux":
                ddm = os.path.join(base_dir, "DepotDownloaderMod")
                cmd = [
                    ddm, "-app", app_id, "-depot", depot_id, "-manifest", manifest_id,
                    "-depotkeys", keyfile_path, "-manifestfile", manifest_file, "-dir", final_download_dir
                ]
                creationflags = 0
            else:
                ddm = os.path.join(base_dir, "DepotDownloaderMod.exe")
                cmd = [
                    ddm, "-app", app_id, "-depot", depot_id, "-manifest", manifest_id,
                    "-depotkeys", keyfile_path, "-manifestfile", manifest_file, "-dir", final_download_dir
                ]
                creationflags = CREATE_NO_WINDOW

            kwargs = {
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "text": True,
                "bufsize": 1,
                "universal_newlines": True
            }

            if platform.system() == "Windows":
                kwargs["creationflags"] = CREATE_NO_WINDOW

            process = subprocess.Popen(cmd, **kwargs)

            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    line = line.strip()
                    match = re.search(r"(\d+(?:\.\d+)?)%", line)
                    if match:
                        try:
                            val = float(match.group(1))
                            overall_progress = ((i * 100) + val) / total_depots
                            self.progress.emit(overall_progress)
                        except ValueError:
                            pass
            
            if process.returncode != 0:
                print(f"DepotDownloader failed with code {process.returncode}")


            os.remove(keyfile_path)

        for root, _, files in os.walk(final_download_dir):
            for filename in files:
                if filename.lower() in ["steam_api.dll", "steam_api64.dll"] and use_goldberg:
                    file_path = os.path.join(root, filename)
                    shutil.move(file_path, file_path.replace(".dll", "_old.dll"))
                    src = os.path.join(base_dir, "goldberg", filename.lower())
                    shutil.copy(src, file_path)
                    with open(os.path.join(root, "steam_appid.txt"), 'w') as f:
                        f.write(app_id)
                if filename.lower().endswith(".exe") and (use_steamless or (platform.system() != "Linux")):
                    file_path = os.path.join(root, filename)
                    steamless = os.path.join(base_dir, "steamless", "Steamless.CLI.exe")
                    if platform.system() == "Linux":
                        subprocess.run([
                            "mono", steamless, "--quiet --realign", file_path
                        ])
                    else:
                        subprocess.run([
                            steamless, "--quiet --realign", file_path
                        ], creationflags=CREATE_NO_WINDOW)
                    if os.path.exists(os.path.join(root, filename + ".unpacked.exe")):
                        shutil.move(file_path, file_path + ".bak")
                        shutil.move(file_path + ".unpacked.exe", file_path)
        return "Done!"

    def __init__(self, extract_path, download_dir, appid, use_steamless=False, use_goldberg=False):
        super().__init__()
        self.extract_path = extract_path
        self.download_dir = download_dir
        self.appid = appid
        self.use_steamless = use_steamless
        self.use_goldberg = use_goldberg

    def run(self):
        self.run_download_logic(self.extract_path, self.download_dir, self.BASE_DIR, self.use_steamless, self.use_goldberg)
        self.finished.emit(0)

class SteamLoaderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steam DDM GUI")
        self.setFixedSize(550, 450)
        self.target_dir = "No directory selected"

        self.setAcceptDrops(True)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; }
            QLabel { color: #e0e0e0; font-family: 'Segoe UI', sans-serif; font-size: 13px; }
            QPushButton {
                background-color: #1e1e1e; color: white; border: 1px solid #333;
                padding: 10px; border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2b2b2b; border-color: #007acc; }
            QPushButton#startButton { background-color: #0e639c; border-color: #1177bb; }
            QPushButton#startButton:hover { background-color: #1177bb; }
            QPushButton#startButton:disabled { background-color: #333; color: #777; border-color: #222; }
            QProgressBar {
                border: 1px solid #333; border-radius: 5px; text-align: center;
                background-color: #1e1e1e; color: white; height: 25px;
            }
            QProgressBar::chunk { background-color: #007acc; width: 10px; }
        """)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        self.path_btn = QPushButton("Select Download Folder")
        self.path_btn.clicked.connect(self.select_directory)
        layout.addWidget(self.path_btn)

        self.dir_label = QLabel(self.target_dir)
        self.dir_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dir_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.dir_label)

        layout.addSpacing(10)

        self.drop_label = QLabel("\n\nDRAG & DROP GAME ZIP HERE\n\n")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #444; border-radius: 10px;
                font-size: 16px; font-weight: bold; color: #666; background: #181818;
            }
        """)
        layout.addWidget(self.drop_label, stretch=1)

        layout.addSpacing(10)

        self.goldberg_checkbox = QCheckBox("Use Goldberg Emulator")
        self.goldberg_checkbox.setChecked(True)
        self.goldberg_checkbox.setStyleSheet("color: #e0e0e0; font-size: 13px;")
        layout.addWidget(self.goldberg_checkbox)

        if platform.system() == "Linux":
            self.steamless_checkbox = QCheckBox("Use Steamless (Requires Mono)")
            self.steamless_checkbox.setStyleSheet("color: #e0e0e0; font-size: 13px;")
            layout.addWidget(self.steamless_checkbox)

        control_layout = QHBoxLayout()

        self.start_btn = QPushButton("START DOWNLOAD")
        self.start_btn.setObjectName("startButton")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.on_start_clicked)
        control_layout.addWidget(self.start_btn)

        self.clear_btn = QPushButton("RESET")
        self.clear_btn.clicked.connect(self.reset_ui)
        control_layout.addWidget(self.clear_btn)

        layout.addLayout(control_layout)

        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.setCentralWidget(central_widget)

        self.current_zip = None
        self.current_appid = None
        self.current_name = None

    def get_game_name(self, appid):
        try:
            url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
            data = requests.get(url, timeout=5).json()
            if data and str(appid) in data and data[str(appid)]['success']:
                return data[str(appid)]['data']['name']
        except: pass
        return f"AppID {appid}"

    def select_directory(self):
        path = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if path:
            self.target_dir = path
            self.dir_label.setText(path)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.drop_label.setStyleSheet("border: 2px dashed #007acc; color: #007acc; background: #1e1e1e;")
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.drop_label.setStyleSheet("border: 2px dashed #444; color: #666; background: #181818;")

    def dropEvent(self, event):
        self.dragLeaveEvent(None)
        files = [u.toLocalFile() for u in event.mimeData().urls()]

        if files and files[0].endswith('.zip'):
            self.current_zip = files[0]
            self.current_appid = os.path.basename(self.current_zip)[:-4]
            self.current_name = self.get_game_name(self.current_appid)

            self.status_label.setText(f"Loaded: {self.current_name}")
            self.start_btn.setEnabled(True)
            self.drop_label.setText(f"\n\n{self.current_name}\nREADY\n\n")

    def on_start_clicked(self):
        if self.target_dir == "No directory selected":
            self.status_label.setText("Select a download folder first!")
            return

        self.start_btn.setEnabled(False)
        self.process_download(self.current_zip, self.current_appid, self.current_name)

    def reset_ui(self):
        self.current_zip = None
        self.current_appid = None
        self.current_name = None
        self.start_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready")
        self.status_label.setStyleSheet("color: #e0e0e0;")
        self.drop_label.setText("\n\nDRAG & DROP GAME ZIP HERE\n\n")

    def process_download(self, zip_path, appid, game_name):
        self.status_label.setText(f"Extracting {game_name}...")

        extract_path = zip_path.replace('.zip', '_temp_meta')
        os.makedirs(extract_path, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(extract_path)

        use_steamless = False
        if platform.system() == 'Linux' and hasattr(self, 'steamless_checkbox'):
            use_steamless = self.steamless_checkbox.isChecked()

        use_goldberg = self.goldberg_checkbox.isChecked()

        self.thread = QThread()
        self.worker = DownloadWorker(extract_path, self.target_dir, appid, use_steamless, use_goldberg)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(lambda p: self.progress_bar.setValue(int(p)))
        self.worker.progress.connect(lambda p: self.status_label.setText(f"Downloading {game_name}: {p}%"))

        self.worker.finished.connect(lambda: self.cleanup_temp(extract_path))

        self.worker.finished.connect(lambda c: self.on_finished(c, game_name))

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def cleanup_temp(self, path):
        try:
            if os.path.exists(path):
                import shutil
                shutil.rmtree(path)
                print(f"Cleaned up temp directory: {path}")
        except Exception as e:
            print(f"Failed to delete temp directory: {e}")

    def on_finished(self, code, name):
        if code == 0:
            self.status_label.setText(f"{name} Installed Successfully!")
            self.progress_bar.setValue(100)
        else:
            self.status_label.setText(f"Error: {name} Failed (Code {code})")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SteamLoaderApp()
    window.show()
    sys.exit(app.exec())
