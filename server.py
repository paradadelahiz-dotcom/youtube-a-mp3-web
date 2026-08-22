import os, re, json, shutil, subprocess, tempfile
import requests
from flask import Flask, jsonify, request, send_from_directory, send_file, Response

ROOT = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=ROOT, static_url_path='')
YOUTUBE_RE = re.compile(r'^https?://(?:(?:www|m)\.)?(?:youtube\.com|youtu\.be)(?:/|$)', re.I)
EXE_DOWNLOAD_URL = os.environ.get('EXE_DOWNLOAD_URL', '').strip()

def valid_url(url):
    return bool(url and YOUTUBE_RE.match(url.strip()))

def yt_info(url):
    cmd=['yt-dlp','--dump-single-json','--no-playlist','--no-warnings','--skip-download',url]
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
    if p.returncode!=0: raise RuntimeError((p.stderr or 'No se pudo obtener el vídeo.').strip()[-1200:])
    data=json.loads(p.stdout)
    return {'id':data.get('id'),'title':data.get('title') or 'Vídeo de YouTube','thumbnail':data.get('thumbnail'),'duration':data.get('duration'),'uploader':data.get('uploader') or data.get('channel'),'webpage_url':data.get('webpage_url') or url}

@app.get('/')
def index(): return send_from_directory(ROOT,'index.html')

@app.post('/api/info')
def api_info():
    body=request.get_json(silent=True) or {}; url=str(body.get('url','')).strip()
    if not valid_url(url): return jsonify(error='Pega una URL válida de YouTube.'),400
    try: return jsonify(yt_info(url))
    except subprocess.TimeoutExpired: return jsonify(error='YouTube ha tardado demasiado en responder.'),504
    except Exception as e: return jsonify(error=f'No se pudo consultar el vídeo: {e}'),502

@app.post('/api/download')
def api_download():
    body=request.get_json(silent=True) or {}; url=str(body.get('url','')).strip()
    if not valid_url(url): return jsonify(error='Pega una URL válida de YouTube.'),400
    tmp=tempfile.mkdtemp(prefix='ytmp3_')
    try:
        out=os.path.join(tmp,'%(title).180s.%(ext)s')
        cmd=['yt-dlp','--no-playlist','--no-warnings','--restrict-filenames','-x','--audio-format','mp3','--audio-quality','192K','-o',out,url]
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=240)
        if p.returncode!=0: raise RuntimeError((p.stderr or p.stdout or 'Error de descarga.').strip()[-1800:])
        files=[os.path.join(tmp,f) for f in os.listdir(tmp) if f.lower().endswith('.mp3')]
        if not files: raise RuntimeError('No se ha generado el MP3.')
        path=files[0]; title=os.path.splitext(os.path.basename(path))[0]
        response=send_file(path,as_attachment=True,download_name=title+'.mp3',mimetype='audio/mpeg')
        @response.call_on_close
        def cleanup(): shutil.rmtree(tmp,ignore_errors=True)
        return response
    except subprocess.TimeoutExpired:
        shutil.rmtree(tmp,ignore_errors=True); return jsonify(error='La descarga ha superado el tiempo máximo.'),504
    except Exception as e:
        shutil.rmtree(tmp,ignore_errors=True); return jsonify(error=f'No se pudo descargar el audio: {e}'),502

@app.get('/api/app-download')
def app_download():
    if not EXE_DOWNLOAD_URL:
        return jsonify(error='Falta configurar EXE_DOWNLOAD_URL en las variables de Railway.'),503
    try:
        upstream=requests.get(EXE_DOWNLOAD_URL,stream=True,timeout=(15,120),allow_redirects=True)
        upstream.raise_for_status()
        headers={'Content-Type':upstream.headers.get('Content-Type','application/octet-stream'),'Content-Disposition':'attachment; filename="YouTube a MP3.exe"'}
        if upstream.headers.get('Content-Length'): headers['Content-Length']=upstream.headers['Content-Length']
        def generate():
            try:
                for chunk in upstream.iter_content(chunk_size=1024*1024):
                    if chunk: yield chunk
            finally: upstream.close()
        return Response(generate(),headers=headers,direct_passthrough=True)
    except requests.RequestException as e:
        return jsonify(error=f'No se pudo obtener el EXE: {e}'),502

if __name__=='__main__':
    port=int(os.environ.get('PORT','8080')); app.run(host='0.0.0.0',port=port)
