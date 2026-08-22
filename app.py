import os
import re
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

    return any(re.search(pattern, url) for pattern in patterns)


@app.route("/")
def index():
    # Primero intenta servir index.html de la raíz
    root_index = BASE_DIR / "index.html"

    if root_index.exists():
        return send_file(root_index)

    # Después intenta templates/index.html
    templates_index = BASE_DIR / "templates" / "index.html"

    if templates_index.exists():
        return send_file(templates_index)

    return """
    <h1>YouTube a MP3</h1>
    <p>No se encontró index.html.</p>
    """, 404


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
        command = [
            "yt-dlp",
            "--dump-single-json",
            "--no-playlist",
            "--skip-download",
            url
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            return jsonify({
                "success": False,
                "error": result.stderr[-1000:]
            }), 500

        import json

        info = json.loads(result.stdout)

        return jsonify({
            "success": True,
            "title": info.get("title", "Vídeo"),
            "channel": info.get("channel")
                       or info.get("uploader")
                       or "",
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "url": url
        })

    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "error": "La búsqueda ha tardado demasiado."
        }), 504

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


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
        output_template = str(
            DOWNLOAD_DIR / "%(title).200B.%(ext)s"
        )

        command = [
            "yt-dlp",
            "--no-playlist",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "192K",
            "-o", output_template,
            url
        ]

        result = subprocess.run(
            command,
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
                "error": "No se ha podido crear el MP3."
            }), 500

        latest_file = max(files, key=lambda f: f.stat().st_mtime)

        return send_file(
            latest_file,
            as_attachment=True,
            download_name=latest_file.name,
            mimetype="audio/mpeg"
        )

    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "error": "La conversión ha tardado demasiado."
        }), 504

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/exe-url")
def exe_url():
    url = os.environ.get("EXE_DOWNLOAD_URL", "").strip()

    if not url:
        return jsonify({
            "success": False,
            "error": "EXE_DOWNLOAD_URL no está configurada."
        }), 404

    return jsonify({
        "success": True,
        "url": url
    })


# Servir archivos estáticos si existe la carpeta static/
@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(
        BASE_DIR / "static",
        filename
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
