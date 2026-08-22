# MP3 YOUTUBE — Web para GitHub + Railway

La interfaz mantiene el estilo blanco/rojo y el botón de cabecera **Descargar** abre un panel con el logo de la aplicación, barra de progreso y botón **Descargar**.

## Descargar el EXE

El EXE no se incluye en el ZIP. En Railway crea una variable:

`EXE_DOWNLOAD_URL`

Pon ahí el enlace público directo a `YouTube a MP3.exe` (por ejemplo, el asset de una GitHub Release).

La web usa `/api/app-download` para hacer de puente y mostrar el progreso real al navegador.

## Convertir YouTube a MP3

La caja principal permite pegar una URL de YouTube, consultar portada/título/duración y descargar el audio MP3 mediante `yt-dlp` + `ffmpeg`.

## Railway

Conecta el repositorio de GitHub con Railway. El proyecto incluye `Dockerfile` y escucha el puerto que Railway proporciona en `PORT`.

Usa el servicio únicamente con contenido que tengas derecho a descargar o para el que tengas permiso.
