import http.server
import socketserver

PORT = 8000

handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("localhost", PORT), handler) as httpd:
    httpd.serve_forever()
