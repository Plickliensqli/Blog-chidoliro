# Blog chidoliro

Blog personal estático para dibujos, escritos y música. Todos los textos, imágenes y audios son archivos propios. No usa bases de datos, servicios de fuentes, rastreadores ni bibliotecas externas en el navegador.

**Dirección prevista:** https://plickliensqli.github.io/Blog-chidoliro/

## Activar el blog por primera vez

1. Abre https://github.com/Plickliensqli/Blog-chidoliro/settings/pages
2. En **Build and deployment → Source**, selecciona **GitHub Actions**.
3. Abre https://github.com/Plickliensqli/Blog-chidoliro/actions y elige **Publicar blog**.
4. Pulsa **Run workflow**, deja la rama `main` y confirma **Run workflow**. Si ya hay una ejecución fallida anterior, puedes usar **Re-run all jobs**.
5. Cuando termine en verde, abre la dirección del blog. La primera publicación puede tardar unos minutos.

## Publicar sin escribir código

1. En el pie del blog abre **Editor**: https://plickliensqli.github.io/Blog-chidoliro/editor/
2. Completa título, sección, fecha y texto. Separa los párrafos con una línea en blanco. El contenido es texto normal; no hace falta escribir Markdown o HTML.
3. Si hay dibujo, sube primero una imagen JPG, PNG o WebP en `assets/imagenes/` desde GitHub: entra a la carpeta, **Add file → Upload files → Commit changes**. Usa nombres sencillos, como `bosque.webp`.
4. En el editor escribe su ruta: `assets/imagenes/bosque.webp`, y describe la imagen. El selector “Ver una imagen de tu equipo” sirve solo para previsualizar: no la sube.
5. Para música, sube un MP3 en `assets/musica/` y escribe su ruta en el editor.
6. Pulsa **Descargar entrada para publicar**. Se descarga un archivo como `mi-primer-dibujo.json`.
7. Sube ese archivo a la carpeta `content/` con **Add file → Upload files → Commit changes**.
8. GitHub generará y publicará el blog automáticamente. Revisa la marca verde de **Actions** antes de recargar.

Si subes primero una imagen o un audio sin su entrada, ese archivo ya será público aunque no aparezca en la portada.

## Guardar un borrador

El editor no guarda automáticamente. Pulsa **Guardar borrador** para descargarlo en tu equipo y usa **Importar entrada** cuando quieras retomarlo. Los borradores tienen `draft: true`, por lo que el generador los omite. **El repositorio es público: no subas borradores privados ni información personal que no quieras compartir.**

## Editar una publicación

En GitHub abre `content/`, elige la entrada y descarga su archivo con **Download raw file**. Impórtalo en el editor. Conserva el campo **Nombre para el enlace**, modifica el texto y vuelve a descargar la entrada para publicar. Sube el JSON a `content/` reemplazando el anterior. Si el navegador añade `(1)` al nombre de la descarga, renómbralo al nombre original antes de subirlo.

La entrada `content/bienvenida.json` es un ejemplo; puedes reemplazarla con tu propio texto. La presentación de “Sobre este espacio” también es genérica.

## Copias de seguridad y cambio de hosting

- Guarda los originales de tus dibujos y proyectos musicales fuera del blog. Sube versiones ligeras para web; usa MP3 para escuchar, no WAV como archivo principal.
- En GitHub pulsa **Code → Download ZIP** para guardar todos los archivos fuente. Guarda otra copia en un disco o servicio distinto. Un ZIP es una copia de archivos, no incluye todo el historial de Git.
- Los archivos publicados se generan en `dist/`. Puedes copiar esa carpeta a cualquier hosting de archivos estáticos, sin depender de GitHub Pages.
- Para conservar también las páginas HTML generadas, descarga el artefacto **github-pages** de una ejecución reciente de Actions o genera el sitio localmente.
- Si cambias de proveedor, modifica `url` y `base_path` en `site.json`, vuelve a generar y sube `dist/`. `base_path` debe ser `""` si el blog estará en la raíz de un dominio.
- Si usas un dominio propio más adelante, recuerda renovarlo y actualizar sus registros al mudar el alojamiento.

## Copia local en tu computadora

Esta carpeta contiene el repositorio Git local vinculado a `Plickliensqli/Blog-chidoliro`, los archivos editables y `dist/` con el sitio generado. Los cambios locales solo llegan a GitHub cuando haces **Commit** y **Push**.

Para ver el blog en tu computadora, haz doble clic en **Abrir-blog.cmd**. Se abrirá una vista previa en tu navegador; deja abierta su ventana mientras la uses. Esto no publica nada en Internet. Python ya está instalado en esta computadora.

Para usar la copia existente con GitHub Desktop, elige **File → Add local repository**, selecciona esta carpeta `blog-personal` y pulsa **Add repository**. Usa **Fetch origin → Pull origin** antes de editar si hiciste cambios desde la web. Para enviar cambios locales: **Commit to main → Push origin**.

En otra computadora puedes clonar el repositorio desde **File → Clone repository → URL** en una carpeta nueva y vacía. No necesitas Python para publicar a través de GitHub; solo para generar o previsualizar localmente.

## Mantenimiento técnico opcional

Solo requiere Python 3.10 o posterior; no se instalan paquetes:

```sh
python build.py
```

Para previsualizar localmente, ajusta `BLOG_BASE_PATH` a una cadena vacía antes de generar y ejecuta un servidor HTTP dentro de `dist/`. En PowerShell:

```powershell
$env:BLOG_BASE_PATH = ""
python build.py
python -m http.server 8000 --directory dist
```

Abre http://localhost:8000. Para volver a usar la configuración de GitHub, elimina esa variable de la sesión antes de regenerar:

```powershell
Remove-Item Env:BLOG_BASE_PATH
python build.py
```

`site.json` controla el título, la firma del autor, la dirección y la descripción. `assets/style.css` controla el diseño. `build.py` genera las páginas, el RSS y el mapa del sitio. El workflow `.github/workflows/publicar.yml` ejecuta el generador y publica `dist/` tras cada cambio en `main`.

El generador comprueba las fechas, categorías, nombres de URL, archivos multimedia y descripciones de imágenes. Si hay un error, Actions no reemplaza la última versión publicada. Revisa el paso **Generar paginas** de la ejecución fallida.

No hay comentarios, inicio de sesión ni cargas directas al servidor. El editor es público pero solo descarga archivos en el equipo de quien lo usa; publicar exige acceso a tu cuenta de GitHub.
