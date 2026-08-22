(function(){
  const modal=document.getElementById('download-modal');
  const openBtn=document.getElementById('open-download');
  const closeEls=modal.querySelectorAll('[data-close-modal]');
  const appBtn=document.getElementById('app-download-btn');
  const appBar=document.getElementById('app-progress-bar');
  const appPercent=document.getElementById('app-percent');
  const appStatus=document.getElementById('app-status');
  const form=document.getElementById('search-form');
  const url=document.getElementById('url');
  const searchBtn=document.getElementById('search-btn');
  const result=document.getElementById('search-result');
  const resultCover=document.getElementById('result-cover');
  const resultTitle=document.getElementById('result-title');
  const resultChannel=document.getElementById('result-channel');
  const resultDuration=document.getElementById('result-duration');
  const resultDownload=document.getElementById('result-download');
  const error=document.getElementById('error');
  let currentUrl='';

  function openModal(){modal.classList.add('is-open');modal.setAttribute('aria-hidden','false');document.body.style.overflow='hidden';}
  function closeModal(){modal.classList.remove('is-open');modal.setAttribute('aria-hidden','true');document.body.style.overflow='';}
  openBtn.addEventListener('click',openModal);
  closeEls.forEach(el=>el.addEventListener('click',closeModal));
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&modal.classList.contains('is-open'))closeModal()});

  function showError(message){error.textContent=message;error.hidden=false;}
  function clearError(){error.hidden=true;error.textContent='';}
  function duration(s){if(!s)return '';s=Math.round(s);return `${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;}

  form.addEventListener('submit',async e=>{
    e.preventDefault();
    const value=url.value.trim();
    clearError(); result.hidden=true;
    if(!value){showError('Pega primero un enlace de YouTube.');return;}
    searchBtn.disabled=true;searchBtn.innerHTML='Buscando…';
    try{
      const r=await fetch('/api/info',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:value})});
      const d=await r.json();
      if(!r.ok)throw Error(d.error||'No se pudo encontrar el vídeo.');
      currentUrl=value;
      resultTitle.textContent=d.title||'Vídeo de YouTube';
      resultChannel.textContent=d.uploader||'YouTube';
      resultDuration.textContent=d.duration?duration(d.duration):'';
      resultCover.src=d.thumbnail||'assets/logo.svg';
      result.hidden=false;
      result.scrollIntoView({behavior:'smooth',block:'center'});
    }catch(err){showError(err.message)}
    finally{searchBtn.disabled=false;searchBtn.innerHTML='Buscar <span aria-hidden="true">→</span>';}
  });

  async function downloadMp3(){
    if(!currentUrl)return;
    clearError(); resultDownload.disabled=true; resultDownload.textContent='Descargando…';
    try{
      const r=await fetch('/api/download',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:currentUrl})});
      if(!r.ok){const d=await r.json().catch(()=>({}));throw Error(d.error||'No se pudo descargar el MP3.');}
      const blob=await r.blob();
      const cd=r.headers.get('Content-Disposition')||'';const m=cd.match(/filename="?([^";]+)"?/i);const name=m?m[1]:'audio.mp3';
      const objectUrl=URL.createObjectURL(blob);const a=document.createElement('a');a.href=objectUrl;a.download=name;document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(objectUrl);
    }catch(err){showError(err.message)}finally{resultDownload.disabled=false;resultDownload.textContent='Descargar';}
  }
  resultDownload.addEventListener('click',downloadMp3);

  async function downloadApp(){
    clearError();appBtn.disabled=true;appBtn.textContent='Descargando…';appStatus.textContent='Preparando descarga…';appBar.style.width='2%';appPercent.textContent='2%';
    try{
      const r=await fetch('/api/app-download');
      if(!r.ok){const d=await r.json().catch(()=>({}));throw Error(d.error||'No se ha configurado el enlace del EXE.');}
      const total=Number(r.headers.get('Content-Length')||0);
      const reader=r.body&&r.body.getReader?r.body.getReader():null;
      let received=0;const chunks=[];
      if(reader){
        while(true){const {done,value}=await reader.read();if(done)break;chunks.push(value);received+=value.byteLength;
          const pct=total?Math.min(99,Math.round(received/total*100)):Math.min(99,Math.round(received/10000000));
          appBar.style.width=pct+'%';appPercent.textContent=pct+'%';appStatus.textContent='Descargando aplicación…';
        }
      }else{appStatus.textContent='Descargando aplicación…';appBar.style.width='50%';appPercent.textContent='50%';chunks.push(new Uint8Array(await r.arrayBuffer()));}
      const blob=new Blob(chunks,{type:'application/octet-stream'});const objectUrl=URL.createObjectURL(blob);const a=document.createElement('a');a.href=objectUrl;a.download='YouTube a MP3.exe';document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(objectUrl);
      appBar.style.width='100%';appPercent.textContent='100%';appStatus.textContent='Descarga completada';
    }catch(err){showError(err.message);appStatus.textContent='No se pudo descargar';appBar.style.width='0%';appPercent.textContent='0%';}
    finally{appBtn.disabled=false;appBtn.textContent='Descargar';}
  }
  appBtn.addEventListener('click',downloadApp);
})();
