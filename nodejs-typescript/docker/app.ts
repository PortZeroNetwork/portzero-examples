import { createServer } from "node:http";

const tunnel = process.env.PZ_TUNNEL ?? "nodejs-typescript-docker.portzero.local:80";

const server = createServer((_request, response) => {
  const address = server.address();
  const port = typeof address === "object" && address !== null ? address.port : 8080;
  const body =
    "Hello from the PortZero Node.js TypeScript Docker example.\n" +
    `PZ_TUNNEL=${tunnel}\n` +
    `container_port=${port}\n`;

  response.writeHead(200, {
    "Content-Type": "text/plain; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
  });
  response.end(body);
});

server.listen(8080, "0.0.0.0");
