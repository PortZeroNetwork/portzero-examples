import { createServer } from "node:http";

const tunnel = process.env.PZ_TUNNEL ?? "nodejs-typescript-process.portzero.local:80";
const tunnelHost = tunnel.split(":", 1)[0];

const server = createServer((_request, response) => {
  const address = server.address();
  const port = typeof address === "object" && address !== null ? address.port : 0;
  const body =
    "Hello from the PortZero Node.js TypeScript process example.\n" +
    `PZ_TUNNEL=${tunnel}\n` +
    `localhost_port=${port}\n`;

  response.writeHead(200, {
    "Content-Type": "text/plain; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
  });
  response.end(body);
});

server.listen(0, "127.0.0.1", () => {
  const address = server.address();
  if (typeof address !== "object" || address === null) {
    throw new Error("Expected Node.js to bind a TCP listener.");
  }

  const port = address.port;
  console.log(
    `PORTZERO_EXAMPLE_LISTENING language=nodejs-typescript variant=process host=127.0.0.1 port=${port} url=http://127.0.0.1:${port}/ tunnel=${tunnel} tunnel_url=http://${tunnelHost}/`,
  );
  console.log(
    `This Node.js TypeScript process was launched with PZ_TUNNEL=${tunnel}. It is now listening on localhost port ${port}. Port Zero detects programs with PZ_TUNNEL listening on a port; the program does not need to read its own PZ_TUNNEL value or detect what port the OS has assigned to it. Technically the program doesn't even need to listen on port 0, although that is highly recommended because avoiding port conflicts is the whole point of using PortZero. The program asked to listen on port 0, so the OS assigned an available port. Next, PortZero's local daemon will detect PZ_TUNNEL and the listening port, then make it available at http://${tunnelHost}/.`,
  );
});
