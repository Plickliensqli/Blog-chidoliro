"""Vista previa local con generación y apertura automática del navegador."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlsplit
import threading
import webbrowser
import build

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(build.OUT), **kwargs)

    def do_GET(self):
        prefix = build.BASE + '/'
        if build.BASE and self.path.startswith(prefix):
            self.path = self.path[len(build.BASE):]
        elif build.BASE and urlsplit(self.path).path == build.BASE:
            self.send_response(302)
            self.send_header('Location', prefix)
            self.end_headers()
            return
        super().do_GET()

if __name__ == '__main__':
    build.build()
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    url = f'http://127.0.0.1:{server.server_port}{build.BASE}/'
    print('Vista previa local: ' + url, flush=True)
    print('Esta vista no publica en Internet. Cierra esta ventana para terminar.', flush=True)
    threading.Timer(0.7, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
