from http.server import HTTPServer, BaseHTTPRequestHandler

HOST = "0.0.0.0"
PORT = 8000


class NeuralHTTP(BaseHTTPRequestHandler):

    def do_GET(self):
        content_request = self.requestline.split(" ")[1][1:]
        if content_request == "hello":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()


        else:
            print(content_request)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()


server = HTTPServer((HOST, PORT), NeuralHTTP)
print("Server now running...")

server.serve_forever()
server.server_close()
print("Server stopped")
