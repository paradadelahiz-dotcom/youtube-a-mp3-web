import os
import re
import json
import tempfile
import subprocess
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = Path(tempfile.gettempdir()) / "youtube_mp3_downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


def valid_youtube_url(url):
    if not url:
        return False

    patterns = [
        r"^https?://(www\.)?youtube\.com/watch\?",
        r"^https?://youtu\.be/",
        r"^https?://(www\.)?youtube\.com/shorts/",
        r"^https?://(www\.)?youtube\.com/embed/",
    ]

    return any(re.search(p, url) for p in patterns)


# =========================
# PÁGINA PRINCIPAL
# =========================

@app.route("/")
def index():
    for name in ("índice.html", "index.html"):
        file = BASE_DIR / name
        if file.exists():
            return send_file(file)

    return "No se encontró el HTML", 404


# =========================
# ARCHIVOS DE LA WEB
# =========================

@app.route("/<path:filename>")
def files(filename):

    # Primero busca archivos directamente en la raíz
    root_file = BASE_DIR / filename

    if root_file.is_file():
        return send_file(root_file)

    # Después busca dentro de activos/
    asset_file = BASE_DIR / "activos" / filename

    if asset_file.is_file():
        return send_file(asset_file)

    return "Archivo no encontrado", 404


# =========================
# INFORMACIÓN DE YOUTUBE
# =========================

@app.route("/api/info", methods=["POST"])
def video_info():

    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()

    if not valid_youtube_url(url):
        return jsonify({
            "success": False,
            "error": "Introduce una URL válida de YouTube."
        }), 400

    try:

        result = subprocess.run(
            [
                "yt-dlp",
                "--dump-single-json",
                "--no-playlist",
                "--skip-download",
                url
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            return jsonify({
                "success": False,
                "error": result.stderr[-1500:]
            }), 500

        info = json.loads(result.stdout)

        return jsonify({
            "success": True,
            "title": info.get("title", "Vídeo"),
            "channel": (
                info.get("channel")
                or info.get("uploader")
                or ""
            ),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "url": url
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================
# DESCARGA MP3
# =========================

@app.route("/api/download", methods=["POST"])
def download_mp3():

    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()

    if not valid_youtube_url(url):
        return jsonify({
            "success": False,
            "error": "URL de YouTube no válida."
        }), 400

    try:

        output = str(
            DOWNLOAD_DIR / "%(title).200B.%(ext)s"
        )

        result = subprocess.run(
            [
                "yt-dlp",
                "--no-playlist",
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "192K",
                "-o", output,
                url
            ],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            return jsonify({
                "success": False,
                "error": result.stderr[-1500:]
            }), 500

        files = list(DOWNLOAD_DIR.glob("*.mp3"))

        if not files:
            return jsonify({
                "success": False,
                "error": "No se pudo crear el MP3."
            }), 500

        latest = max(
            files,
            key=lambda f: f.stat().st_mtime
        )

        return send_file(
            latest,
            as_attachment=True,
            download_name=latest.name,
            mimetype="audio/mpeg"
        )

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================
# URL DEL EXE
# =========================

@app.route("/api/exe-url")
def exe_url():

    url = os.environ.get("EXE_DOWNLOAD_URL", "").strip()

    if not url:
        return jsonify({
            "success": False,
            "error": "EXE_DOWNLOAD_URL no configurada."
        }), 404

    return jsonify({
        "success": True,
        "url": url
    })


# =========================
# ARRANQUE
# =========================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", "8080"))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
