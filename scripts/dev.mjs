#!/usr/bin/env node

import { spawn, spawnSync } from "node:child_process";

run("npm", ["run", "mock:db:push"]);
run("npm", ["run", "mock:db:seed"]);

const processes = [
  spawn("npm", ["run", "mock:api"], { stdio: "inherit" }),
  spawn("npm", ["run", "dev:web"], { stdio: "inherit" }),
];

let stopping = false;

for (const child of processes) {
  child.on("exit", (code) => {
    if (!stopping && code !== 0) {
      stop();
      process.exit(code ?? 1);
    }
  });
}

process.on("SIGINT", stop);
process.on("SIGTERM", stop);

function run(command, args) {
  const result = spawnSync(command, args, { stdio: "inherit" });
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

function stop() {
  stopping = true;
  for (const child of processes) {
    if (!child.killed) child.kill("SIGTERM");
  }
}
