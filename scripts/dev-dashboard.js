import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
const publicDir = join(root, "public");
const reportsDir = join(root, "reports");
const port = Number(process.env.PORT || 8765);

const contentTypes = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml"
};

createServer(async (request, response) => {
  const url = new URL(request.url || "/", `http://localhost:${port}`);

  try {
    if (url.pathname === "/api/health") {
      return sendJson(response, { ok: true, mode: "local", now: new Date().toISOString() });
    }

    if (url.pathname === "/api/live-history") {
      const history = await readFile(join(reportsDir, "live_account_history.json"), "utf8");
      response.writeHead(200, { "content-type": "application/json; charset=utf-8" });
      return response.end(history);
    }

    if (url.pathname === "/api/live-current") {
      const history = JSON.parse(await readFile(join(reportsDir, "live_account_history.json"), "utf8"));
      const current = Array.isArray(history) && history.length > 0 ? history[history.length - 1] : {};
      return sendJson(response, current);
    }

    const requested = url.pathname === "/" ? "/index.html" : url.pathname;
    const path = normalize(join(publicDir, requested));
    if (!path.startsWith(publicDir)) {
      response.writeHead(403);
      return response.end("Forbidden");
    }

    const body = await readFile(path);
    response.writeHead(200, { "content-type": contentTypes[extname(path)] || "application/octet-stream" });
    return response.end(body);
  } catch (error) {
    response.writeHead(error.code === "ENOENT" ? 404 : 500, { "content-type": "text/plain; charset=utf-8" });
    return response.end(String(error.message || error));
  }
}).listen(port, () => {
  console.log(`Trader dashboard running at http://127.0.0.1:${port}/`);
});

function sendJson(response, data) {
  response.writeHead(200, { "content-type": "application/json; charset=utf-8" });
  response.end(JSON.stringify(data, null, 2));
}
