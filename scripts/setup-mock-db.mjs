#!/usr/bin/env node

import { existsSync, mkdirSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { spawnSync } from "node:child_process";

const shouldReset = process.argv.includes("--reset");
const dbPath = resolve("prisma/dev.db");
const schemaPath = "prisma/schema.prisma";

if (shouldReset && existsSync(dbPath)) {
  rmSync(dbPath);
}

mkdirSync(dirname(dbPath), { recursive: true });

run("npx", ["prisma", "generate"]);

if (existsSync(dbPath) && !shouldReset) {
  console.log(`Mock database already exists: ${dbPath}`);
  process.exit(0);
}

const diff = spawnSync(
  "npx",
  ["prisma", "migrate", "diff", "--from-empty", "--to-schema-datamodel", schemaPath, "--script"],
  { encoding: "utf8" },
);

if (diff.status !== 0) {
  process.stdout.write(diff.stdout);
  process.stderr.write(diff.stderr);
  process.exit(diff.status ?? 1);
}

const sqlite = spawnSync("sqlite3", [dbPath], {
  input: `${diff.stdout}\n`,
  encoding: "utf8",
});

if (sqlite.status !== 0) {
  process.stdout.write(sqlite.stdout);
  process.stderr.write(sqlite.stderr);
  process.exit(sqlite.status ?? 1);
}

console.log(`Mock database schema is ready: ${dbPath}`);

function run(command, args) {
  const result = spawnSync(command, args, { stdio: "inherit" });
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}
