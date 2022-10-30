from ivt490 import latestLineAsJson
from http.server import BaseHTTPRequestHandler, HTTPServer

port = 10490
basepath = "/media/passport/dump/ivt490"

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        json = latestLineAsJson(basepath)

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        self.wfile.write(bytes(json, "utf-8"))

def run():
    print(f"Starting HTTP server on port {port}")
    server_address = ('', port)
    httpd = HTTPServer(server_address, MyHandler)
    httpd.serve_forever()

if __name__ == "__main__":
    run()
