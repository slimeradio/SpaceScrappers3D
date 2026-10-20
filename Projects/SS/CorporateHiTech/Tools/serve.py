from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from functools import partial
SimpleHTTPRequestHandler.extensions_map.update({'.js':'text/javascript','.cjs':'text/javascript','.json':'application/json','.gltf':'model/gltf+json'})
root=Path(__file__).resolve().parents[1]
class ViewerHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        from urllib.parse import urlsplit
        url_path = urlsplit(path).path
        if url_path.startswith('/Viewer/vendor/'):
            vendor = root.parents[2] / 'Viewer' / 'vendor'
            target = (vendor / url_path[len('/Viewer/vendor/'):]).resolve()
            if target.is_relative_to(vendor.resolve()):
                return str(target)
            return str(vendor / '__invalid_path__')
        return super().translate_path(path)

print('CorporateHiTech: http://127.0.0.1:8768/Blocks/CHT-T01/viewer.html',flush=True)
ThreadingHTTPServer(('127.0.0.1',8768),partial(ViewerHandler,directory=str(root))).serve_forever()
