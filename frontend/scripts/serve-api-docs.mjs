#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontendDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const rootDir = resolve(frontendDir, "..");
const outputDir = process.env.OPENAPI_OUT_DIR || join(tmpdir(), "calendar-typespec-output");
const openapiDir = join(outputDir, "@typespec", "openapi3");
const openapiJsonPath = join(openapiDir, "calendar.openapi.json");
const openapiYamlPath = join(openapiDir, "calendar.openapi.yaml");
const port = getPort();

compileTypeSpec();

const server = createServer((request, response) => {
  const url = new URL(request.url ?? "/", `http://${request.headers.host ?? "localhost"}`);

  if (url.pathname === "/") {
    send(response, 200, "text/html; charset=utf-8", renderHtml());
    return;
  }

  if (url.pathname === "/openapi.json") {
    sendFile(response, "application/json; charset=utf-8", openapiJsonPath);
    return;
  }

  if (url.pathname === "/openapi.yaml") {
    sendFile(response, "application/yaml; charset=utf-8", openapiYamlPath);
    return;
  }

  if (url.pathname === "/healthz") {
    send(response, 200, "text/plain; charset=utf-8", "ok\n");
    return;
  }

  send(response, 404, "text/plain; charset=utf-8", "Not found\n");
});

server.listen(port, "127.0.0.1", () => {
  console.log(`API docs: http://127.0.0.1:${port}`);
  console.log(`OpenAPI JSON: http://127.0.0.1:${port}/openapi.json`);
  console.log(`OpenAPI YAML: http://127.0.0.1:${port}/openapi.yaml`);
});

function getPort() {
  const portArg = process.argv.find((arg) => arg.startsWith("--port="));
  const rawPort = process.env.PORT || portArg?.slice("--port=".length) || "8080";
  const parsedPort = Number(rawPort);

  if (!Number.isInteger(parsedPort) || parsedPort < 1 || parsedPort > 65535) {
    throw new Error(`Invalid port: ${rawPort}`);
  }

  return parsedPort;
}

function compileTypeSpec() {
  const tspBin = join(frontendDir, "node_modules", ".bin", "tsp");
  const result = spawnSync(tspBin, ["compile", "spec", "--output-dir", outputDir], {
    cwd: rootDir,
    stdio: "inherit",
  });

  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }

  if (!existsSync(openapiJsonPath)) {
    throw new Error(`OpenAPI JSON was not generated: ${openapiJsonPath}`);
  }
}

function sendFile(response, contentType, filePath) {
  if (!existsSync(filePath)) {
    send(response, 404, "text/plain; charset=utf-8", `File not found: ${filePath}\n`);
    return;
  }

  send(response, 200, contentType, readFileSync(filePath));
}

function send(response, statusCode, contentType, body) {
  response.writeHead(statusCode, {
    "content-type": contentType,
    "cache-control": "no-store",
  });
  response.end(body);
}

function renderHtml() {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Calendar API Docs</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --line: #dfe3ea;
      --text: #17202a;
      --muted: #667085;
      --accent: #2563eb;
      --get: #166534;
      --post: #1d4ed8;
      --patch: #a16207;
      --delete: #b42318;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font: 14px/1.5 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    header {
      position: sticky;
      top: 0;
      z-index: 2;
      display: flex;
      gap: 16px;
      align-items: center;
      justify-content: space-between;
      padding: 16px 24px;
      background: var(--panel);
      border-bottom: 1px solid var(--line);
    }

    h1, h2, h3, p {
      margin: 0;
    }

    h1 {
      font-size: 20px;
      line-height: 1.2;
    }

    a {
      color: var(--accent);
      text-decoration: none;
    }

    a:hover {
      text-decoration: underline;
    }

    .layout {
      display: grid;
      grid-template-columns: 300px minmax(0, 1fr);
      min-height: calc(100vh - 65px);
    }

    aside {
      position: sticky;
      top: 65px;
      height: calc(100vh - 65px);
      overflow: auto;
      padding: 20px;
      background: var(--panel);
      border-right: 1px solid var(--line);
    }

    main {
      max-width: 1180px;
      width: 100%;
      padding: 24px;
    }

    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      color: var(--muted);
      font-size: 13px;
    }

    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }

    .button {
      display: inline-flex;
      min-height: 34px;
      align-items: center;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 6px 10px;
      background: #fff;
      color: var(--text);
    }

    .search {
      width: 100%;
      margin-bottom: 16px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 9px 10px;
      font: inherit;
    }

    .nav-title {
      margin: 18px 0 8px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: .04em;
    }

    .nav-link {
      display: block;
      padding: 6px 0;
      overflow: hidden;
      color: var(--text);
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .section {
      margin-bottom: 28px;
    }

    .section h2 {
      margin-bottom: 12px;
      font-size: 20px;
    }

    .operation {
      margin-bottom: 12px;
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
    }

    .operation summary {
      display: grid;
      grid-template-columns: 80px minmax(0, 1fr);
      gap: 12px;
      align-items: center;
      cursor: pointer;
      padding: 12px 14px;
    }

    .method {
      display: inline-flex;
      justify-content: center;
      border-radius: 5px;
      padding: 4px 8px;
      color: #fff;
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
    }

    .method.get { background: var(--get); }
    .method.post { background: var(--post); }
    .method.patch { background: var(--patch); }
    .method.delete { background: var(--delete); }

    .path {
      overflow-wrap: anywhere;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-weight: 650;
    }

    .operation-body {
      display: grid;
      gap: 16px;
      padding: 0 14px 14px;
      border-top: 1px solid var(--line);
    }

    .subgrid {
      display: grid;
      gap: 8px;
    }

    .muted {
      color: var(--muted);
    }

    code, pre {
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }

    pre {
      overflow: auto;
      max-height: 360px;
      margin: 0;
      border-radius: 6px;
      padding: 12px;
      background: #111827;
      color: #f9fafb;
      font-size: 12px;
    }

    .pill-list {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }

    .pill {
      display: inline-flex;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 2px 8px;
      background: #fff;
      color: var(--muted);
      font-size: 12px;
    }

    .schema-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 12px;
    }

    .schema {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
    }

    .schema summary {
      cursor: pointer;
      padding: 10px 12px;
      font-weight: 650;
    }

    .schema pre {
      border-radius: 0 0 8px 8px;
    }

    @media (max-width: 840px) {
      header {
        align-items: flex-start;
        flex-direction: column;
      }

      .layout {
        grid-template-columns: 1fr;
      }

      aside {
        position: static;
        height: auto;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }

      main {
        padding: 16px;
      }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1 id="title">Calendar API</h1>
      <div class="meta" id="meta"></div>
    </div>
    <nav class="toolbar">
      <a class="button" href="/openapi.json">OpenAPI JSON</a>
      <a class="button" href="/openapi.yaml">OpenAPI YAML</a>
    </nav>
  </header>
  <div class="layout">
    <aside>
      <input class="search" id="search" type="search" placeholder="Filter paths, tags, operation IDs" />
      <div id="nav"></div>
    </aside>
    <main>
      <section class="section" id="operations"></section>
      <section class="section">
        <h2>Schemas</h2>
        <div class="schema-grid" id="schemas"></div>
      </section>
    </main>
  </div>
  <script>
    const methods = ["get", "post", "put", "patch", "delete", "options", "head", "trace"];
    const state = { spec: null, filter: "" };

    document.getElementById("search").addEventListener("input", (event) => {
      state.filter = event.target.value.trim().toLowerCase();
      render();
    });

    fetch("/openapi.json")
      .then((response) => {
        if (!response.ok) throw new Error("Failed to load OpenAPI JSON");
        return response.json();
      })
      .then((spec) => {
        state.spec = spec;
        render();
      })
      .catch((error) => {
        document.getElementById("operations").innerHTML =
          '<p class="muted">' + escapeHtml(error.message) + "</p>";
      });

    function render() {
      if (!state.spec) return;

      const spec = state.spec;
      const title = spec.info?.title || "API";
      const version = spec.info?.version || "unknown";
      const server = spec.servers?.[0]?.url || "";
      const operations = getOperations(spec).filter(matchesFilter);
      const groups = groupByTag(operations);

      document.getElementById("title").textContent = title;
      document.getElementById("meta").innerHTML = [
        "version " + escapeHtml(version),
        server ? "server " + escapeHtml(server) : "",
        operations.length + " operations"
      ].filter(Boolean).map((item) => "<span>" + item + "</span>").join("");

      renderNav(groups);
      renderOperations(groups);
      renderSchemas(spec.components?.schemas || {});
    }

    function getOperations(spec) {
      return Object.entries(spec.paths || {}).flatMap(([path, pathItem]) =>
        methods
          .filter((method) => pathItem[method])
          .map((method) => ({
            path,
            method,
            operation: pathItem[method],
            tag: pathItem[method].tags?.[0] || "Other",
          }))
      );
    }

    function matchesFilter(item) {
      if (!state.filter) return true;
      const haystack = [
        item.path,
        item.method,
        item.tag,
        item.operation.operationId,
        item.operation.summary,
      ].filter(Boolean).join(" ").toLowerCase();
      return haystack.includes(state.filter);
    }

    function groupByTag(operations) {
      return operations.reduce((groups, item) => {
        groups[item.tag] ??= [];
        groups[item.tag].push(item);
        return groups;
      }, {});
    }

    function renderNav(groups) {
      const nav = Object.entries(groups).map(([tag, operations]) => {
        const links = operations.map((item) => {
          const id = operationDomId(item);
          return '<a class="nav-link" href="#' + id + '">' +
            '<span class="method ' + item.method + '">' + item.method + '</span> ' +
            escapeHtml(item.path) +
            '</a>';
        }).join("");
        return '<div class="nav-title">' + escapeHtml(tag) + '</div>' + links;
      }).join("");
      document.getElementById("nav").innerHTML = nav || '<p class="muted">No operations found.</p>';
    }

    function renderOperations(groups) {
      const html = Object.entries(groups).map(([tag, operations]) => {
        const cards = operations.map(renderOperation).join("");
        return '<div class="section"><h2>' + escapeHtml(tag) + '</h2>' + cards + '</div>';
      }).join("");
      document.getElementById("operations").innerHTML = html || '<p class="muted">No operations found.</p>';
    }

    function renderOperation(item) {
      const op = item.operation;
      const responses = Object.keys(op.responses || {});
      const params = op.parameters || [];
      const requestSchema = op.requestBody?.content?.["application/json"]?.schema;

      return '<details class="operation" id="' + operationDomId(item) + '">' +
        '<summary>' +
          '<span class="method ' + item.method + '">' + item.method + '</span>' +
          '<span class="path">' + escapeHtml(item.path) + '</span>' +
        '</summary>' +
        '<div class="operation-body">' +
          '<div class="subgrid">' +
            '<h3>' + escapeHtml(op.summary || op.operationId || item.path) + '</h3>' +
            '<div class="muted"><code>' + escapeHtml(op.operationId || "") + '</code></div>' +
          '</div>' +
          renderParameters(params) +
          renderRequestBody(requestSchema) +
          '<div class="subgrid"><strong>Responses</strong><div class="pill-list">' +
            responses.map((status) => '<span class="pill">' + escapeHtml(status) + '</span>').join("") +
          '</div></div>' +
        '</div>' +
      '</details>';
    }

    function renderParameters(params) {
      if (!params.length) return "";
      const pills = params.map((param) =>
        '<span class="pill">' + escapeHtml(param.in + " " + param.name + (param.required ? " required" : "")) + '</span>'
      ).join("");
      return '<div class="subgrid"><strong>Parameters</strong><div class="pill-list">' + pills + '</div></div>';
    }

    function renderRequestBody(schema) {
      if (!schema) return "";
      return '<div class="subgrid"><strong>Request body</strong><pre>' +
        escapeHtml(JSON.stringify(schema, null, 2)) +
      '</pre></div>';
    }

    function renderSchemas(schemas) {
      const html = Object.entries(schemas).map(([name, schema]) =>
        '<details class="schema">' +
          '<summary>' + escapeHtml(name) + '</summary>' +
          '<pre>' + escapeHtml(JSON.stringify(schema, null, 2)) + '</pre>' +
        '</details>'
      ).join("");
      document.getElementById("schemas").innerHTML = html || '<p class="muted">No schemas found.</p>';
    }

    function operationDomId(item) {
      return "op-" + btoa(item.method + " " + item.path)
        .replaceAll("=", "")
        .replaceAll("+", "-")
        .replaceAll("/", "_");
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }
  </script>
</body>
</html>`;
}
