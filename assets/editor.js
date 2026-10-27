(() => {
  const form = document.querySelector('#post-form');
  if (!form) return;
  const keys = ['title','category','date','slug','excerpt','text','image','image_alt','audio'];
  const field = key => document.getElementById(key);
  const status = document.querySelector('#editor-status');
  const today = new Date();
  field('date').value = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;
  const slugify = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,100).replace(/-$/,'');
  let customSlug = false, changed = false, imageUrl = '';
  field('slug').addEventListener('input', () => { customSlug = true; });
  function preview() {
    if (!customSlug) field('slug').value = slugify(field('title').value);
    field('preview-title').textContent = field('title').value || 'El título de tu publicación';
    field('preview-excerpt').textContent = field('excerpt').value;
    field('preview-text').textContent = field('text').value || 'Las ideas empiezan con una primera línea.';
    field('preview-image').alt = field('image_alt').value;
  }
  form.addEventListener('input', () => { changed = true; preview(); });
  function data(draft=false) {
    const result = Object.fromEntries(keys.map(k => [k,field(k).value.trim()]));
    result.text = field('text').value.trim().replace(/\r\n/g,'\n');
    if (draft) result.draft = true;
    return result;
  }
  function valid(post) {
    for (const key of ['image','audio']) {
      if (post[key] && (!post[key].startsWith('assets/') || post[key].includes('\\') || post[key].split('/').includes('..') || /[?#]/.test(post[key]))) {
        status.textContent = 'Usa una ruta local que empiece por assets/, sin enlaces externos ni ../.';
        return false;
      }
    }
    if (post.image && !post.image_alt) { status.textContent = 'Añade una descripción para la imagen.'; field('image_alt').focus(); return false; }
    return true;
  }
  function download(draft) {
    if (!draft && !form.reportValidity()) return;
    const post = data(draft);
    if (!draft && !valid(post)) return;
    const blob = new Blob([JSON.stringify(post,null,2)+'\n'], {type:'application/json;charset=utf-8'});
    const url = URL.createObjectURL(blob), a = document.createElement('a');
    a.href = url; a.download = `${post.slug || 'borrador'}.json`;
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url),1000);
    changed = false;
    status.textContent = draft ? 'Borrador descargado. Guárdalo en tu equipo; no está publicado.' : 'Entrada descargada. Falta subirla a la carpeta content de GitHub para publicarla.';
  }
  form.addEventListener('submit', event => { event.preventDefault(); download(false); });
  field('draft').addEventListener('click', () => download(true));
  field('import').addEventListener('change', async event => {
    const file = event.target.files[0]; if (!file) return;
    if (changed && !confirm('Hay cambios sin descargar. ¿Quieres reemplazarlos con este archivo?')) { event.target.value = ''; return; }
    try {
      if (file.size > 2*1024*1024) throw Error('El archivo es demasiado grande para ser una entrada.');
      const post = JSON.parse(await file.text());
      if (!post || typeof post !== 'object' || Array.isArray(post) || typeof post.title !== 'string' || typeof post.text !== 'string') throw Error('No parece una entrada de este blog.');
      if (!['escritos','dibujos','musica'].includes(post.category)) throw Error('La categoría no es válida.');
      keys.forEach(k => { field(k).value = typeof post[k] === 'string' ? post[k] : ''; });
      customSlug = true; changed = false;
      if (imageUrl) URL.revokeObjectURL(imageUrl);
      imageUrl = ''; field('preview-image').hidden = true; field('image-preview').value = '';
      preview(); status.textContent = post.draft ? 'Borrador importado. La descarga para publicar quitará la marca de borrador.' : 'Entrada importada. Conserva su nombre para el enlace al editarla.';
    } catch(error) { status.textContent = 'No se pudo importar: ' + error.message; }
    event.target.value = '';
  });
  field('image-preview').addEventListener('change', event => {
    if (imageUrl) URL.revokeObjectURL(imageUrl);
    const file = event.target.files[0];
    if (!file) { field('preview-image').hidden = true; return; }
    if (!['image/jpeg','image/png','image/webp','image/gif'].includes(file.type)) { status.textContent = 'Selecciona una imagen PNG, JPG, WebP o GIF.'; return; }
    imageUrl = URL.createObjectURL(file); field('preview-image').src = imageUrl; field('preview-image').hidden = false;
  });
  addEventListener('beforeunload', event => { if (changed) { event.preventDefault(); event.returnValue = ''; } });
  preview();
})();
