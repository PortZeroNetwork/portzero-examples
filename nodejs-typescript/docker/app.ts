import { createServer } from "node:http";

const tunnel = process.env.PZ_TUNNEL ?? "nodejs-typescript-docker.portzero.local:80";

const server = createServer((_request, response) => {
  const body =
    "Hello from the PortZero Node.js TypeScript Docker example.\n" +
    `PZ_TUNNEL=${tunnel}\n` +
    "container_port=8080\n";

  response.writeHead(200, {
    "Content-Type": "text/plain; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
  });
  response.end(body);
});

server.listen(8080, "0.0.0.0");
