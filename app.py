(function () {

  "use strict";


  /* ==================================================
     ELEMENTOS
  ================================================== */

  const modal = document.getElementById("download-modal");
  const openBtn = document.getElementById("open-download");

  const closeEls = modal
    ? modal.querySelectorAll("[data-close-modal]")
    : [];

  const appBtn = document.getElementById("app-download-btn");
  const appBar = document.getElementById("app-progress-bar");
  const appPercent = document.getElementById("app-percent");
  const appStatus = document.getElementById("app-status");

  const form = document.getElementById("search-form");
  const urlInput = document.getElementById("url");
  const searchBtn = document.getElementById("search-btn");

  const result = document.getElementById("search-result");
  const resultCover = document.getElementById("result-cover");
  const resultTitle = document.getElementById("result-title");
  const resultChannel = document.getElementById("result-channel");
  const resultDuration = document.getElementById("result-duration");
  const resultDownload = document.getElementById("result-download");

  const error = document.getElementById("error");


  let currentUrl = "";


  /* ==================================================
     MODAL
  ================================================== */

  function openModal() {

    if (!modal) return;

    modal.classList.add("is-open");

    modal.setAttribute(
      "aria-hidden",
      "false"
    );

    document.body.style.overflow = "hidden";

  }


  function closeModal() {

    if (!modal) return;

    modal.classList.remove("is-open");

    modal.setAttribute(
      "aria-hidden",
      "true"
    );

    document.body.style.overflow = "";

  }


  if (openBtn) {

    openBtn.addEventListener(
      "click",
      openModal
    );

  }


  closeEls.forEach(function (element) {

    element.addEventListener(
      "click",
      closeModal
    );

  });


  document.addEventListener(
    "keydown",
    function (event) {

      if (
        event.key === "Escape" &&
        modal &&
        modal.classList.contains("is-open")
      ) {

        closeModal();

      }

    }
  );


  /* ==================================================
     ERRORES
  ================================================== */

  function showError(message) {

    if (!error) return;

    error.textContent = message;

    error.hidden = false;

  }


  function clearError() {

    if (!error) return;

    error.textContent = "";

    error.hidden = true;

  }


  /* ==================================================
     DURACIÓN
  ================================================== */

  function duration(seconds) {

    if (!seconds) {
      return "";
    }

    seconds = Math.round(
      Number(seconds)
    );

    const minutes = Math.floor(
      seconds / 60
    );

    const remaining = String(
      seconds % 60
    ).padStart(2, "0");

    return minutes + ":" + remaining;

  }


  /* ==================================================
     BÚSQUEDA DE YOUTUBE
  ================================================== */

  if (form) {

    form.addEventListener(
      "submit",
      async function (event) {

        event.preventDefault();

        clearError();

        if (result) {
          result.hidden = true;
        }


        const value = urlInput
          ? urlInput.value.trim()
          : "";


        if (!value) {

          showError(
            "Pega primero un enlace de YouTube."
          );

          return;

        }


        searchBtn.disabled = true;

        searchBtn.innerHTML =
          "Buscando…";


        try {

          const response = await fetch(
            "/api/info",
            {
              method: "POST",

              headers: {
                "Content-Type":
                  "application/json"
              },

              body: JSON.stringify({
                url: value
              })
            }
          );


          const data =
            await response.json();


          if (!response.ok || !data.success) {

            throw new Error(
              data.error ||
              "No se pudo encontrar el vídeo."
            );

          }


          /* GUARDAR URL */

          currentUrl = value;


          /* TÍTULO */

          resultTitle.textContent =
            data.title ||
            "Vídeo de YouTube";


          /* CANAL */

          resultChannel.textContent =
            data.channel ||
            "YouTube";


          /* DURACIÓN */

          resultDuration.textContent =
            data.duration
              ? duration(data.duration)
              : "";


          /* ==================================================
             PORTADA DE YOUTUBE
          ================================================== */

          if (data.thumbnail) {

            resultCover.src =
              data.thumbnail;

            resultCover.alt =
              data.title ||
              "Portada del vídeo";


            /*
             * Si la miniatura falla,
             * volvemos al logo de la aplicación.
             */

            resultCover.onerror =
              function () {

                this.onerror = null;

                this.src =
                  "/static/logo.svg";

              };

          } else {

            resultCover.src =
              "/static/logo.svg";

          }


          /* MOSTRAR RESULTADO */

          result.hidden = false;


          /* ANIMACIÓN */

          if (result.animate) {

            result.animate(
              [
                {
                  opacity: 0,
                  transform:
                    "translateY(15px)"
                },

                {
                  opacity: 1,
                  transform:
                    "translateY(0)"
                }
              ],
              {
                duration: 350,
                easing:
                  "ease-out"
              }
            );

          }


          /* SCROLL */

          setTimeout(
            function () {

              result.scrollIntoView({
                behavior: "smooth",
                block: "center"
              });

            },
            50
          );


        } catch (err) {

          showError(
            err.message ||
            "Ha ocurrido un error."
          );

        } finally {

          searchBtn.disabled = false;

          searchBtn.innerHTML =
            'Buscar <span aria-hidden="true">→</span>';

        }

      }
    );

  }


  /* ==================================================
     DESCARGAR MP3
  ================================================== */

  async function downloadMp3() {

    if (!currentUrl) {

      showError(
        "Primero busca un vídeo."
      );

      return;

    }


    clearError();

    resultDownload.disabled = true;

    resultDownload.textContent =
      "Descargando…";


    try {

      const response = await fetch(
        "/api/download",
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json"
          },

          body: JSON.stringify({
            url: currentUrl
          })
        }
      );


      if (!response.ok) {

        const data =
          await response
            .json()
            .catch(function () {
              return {};
            });


        throw new Error(
          data.error ||
          "No se pudo descargar el MP3."
        );

      }


      /* OBTENER ARCHIVO */

      const blob =
        await response.blob();


      /* NOMBRE */

      const contentDisposition =
        response.headers.get(
          "Content-Disposition"
        ) || "";


      let filename =
        "audio.mp3";


      const match =
        contentDisposition.match(
          /filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i
        );


      if (match) {

        filename =
          decodeURIComponent(
            match[1] ||
            match[2]
          );

      }


      /* DESCARGA */

      const objectUrl =
        URL.createObjectURL(blob);


      const link =
        document.createElement("a");


      link.href = objectUrl;

      link.download = filename;

      document.body.appendChild(link);

      link.click();

      link.remove();


      setTimeout(
        function () {

          URL.revokeObjectURL(
            objectUrl
          );

        },
        1000
      );


    } catch (err) {

      showError(
        err.message ||
        "No se pudo descargar el MP3."
      );

    } finally {

      resultDownload.disabled = false;

      resultDownload.textContent =
        "Descargar";

    }

  }


  if (resultDownload) {

    resultDownload.addEventListener(
      "click",
      downloadMp3
    );

  }


  /* ==================================================
     DESCARGA DE LA APLICACIÓN EXE
  ================================================== */

  async function downloadApp() {

    clearError();


    appBtn.disabled = true;

    appBtn.textContent =
      "Preparando…";


    appStatus.textContent =
      "Preparando descarga…";


    appBar.style.width =
      "2%";


    appPercent.textContent =
      "2%";


    try {

      /*
       * Primero obtenemos la URL pública
       * configurada en Railway.
       */

      const infoResponse =
        await fetch(
          "/api/exe-url",
          {
            cache: "no-store"
          }
        );


      const info =
        await infoResponse
          .json()
          .catch(function () {
            return {};
          });


      if (
        !infoResponse.ok ||
        !info.success ||
        !info.url
      ) {

        throw new Error(
          info.error ||
          "No se ha configurado el enlace del EXE."
        );

      }


      /*
       * Si tenemos una URL pública,
       * iniciamos la descarga.
       */

      appStatus.textContent =
        "Descargando aplicación…";


      appBar.style.width =
        "20%";


      appPercent.textContent =
        "20%";


      const response =
        await fetch(
          info.url
        );


      if (!response.ok) {

        throw new Error(
          "No se pudo descargar la aplicación."
        );

      }


      /*
       * Intentamos mostrar progreso real.
       */

      const total =
        Number(
          response.headers.get(
            "Content-Length"
          ) || 0
        );


      const reader =
        response.body &&
        response.body.getReader
          ? response.body.getReader()
          : null;


      let received = 0;

      const chunks = [];


      if (reader) {

        while (true) {

          const result =
            await reader.read();


          if (result.done) {
            break;
          }


          chunks.push(
            result.value
          );


          received +=
            result.value.byteLength;


          let percent;


          if (total > 0) {

            percent =
              Math.round(
                received /
                total *
                100
              );

          } else {

            percent =
              Math.min(
                99,
                20 +
                Math.round(
                  received /
                  10000000 *
                  79
                )
              );

          }


          percent =
            Math.min(
              99,
              Math.max(
                2,
                percent
              )
            );


          appBar.style.width =
            percent + "%";


          appPercent.textContent =
            percent + "%";


          appStatus.textContent =
            "Descargando aplicación…";

        }

      } else {

        const buffer =
          await response.arrayBuffer();


        chunks.push(
          new Uint8Array(buffer)
        );


        appBar.style.width =
          "90%";


        appPercent.textContent =
          "90%";

      }


      /* CREAR EXE */

      const blob =
        new Blob(
          chunks,
          {
            type:
              "application/octet-stream"
          }
        );


      const objectUrl =
        URL.createObjectURL(
          blob
        );


      const link =
        document.createElement("a");


      link.href =
        objectUrl;


      link.download =
        "YouTube a MP3.exe";


      document.body.appendChild(
        link
      );


      link.click();


      link.remove();


      setTimeout(
        function () {

          URL.revokeObjectURL(
            objectUrl
          );

        },
        2000
      );


      /* 100% */

      appBar.style.width =
        "100%";


      appPercent.textContent =
        "100%";


      appStatus.textContent =
        "Descarga completada";


    } catch (err) {

      showError(
        err.message ||
        "No se pudo descargar la aplicación."
      );


      appStatus.textContent =
        "No se pudo descargar";


      appBar.style.width =
        "0%";


      appPercent.textContent =
        "0%";

    } finally {

      appBtn.disabled = false;

      appBtn.textContent =
        "Descargar";

    }

  }


  if (appBtn) {

    appBtn.addEventListener(
      "click",
      downloadApp
    );

  }


})();
