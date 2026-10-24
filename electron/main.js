"use strict";

const { app, BrowserWindow, Menu, shell, dialog, ipcMain } = require("electron");
const { spawn, execFile } = require("child_process");
const fs = require("fs");
const path = require("path");
const http = require("http");

const IS_PACKAGED = app.isPackaged;
const API_PORT = process.env.HALLWAY_PORT ? Number(process.env.HALLWAY_PORT) : 8000;
const API_HOST = "127.0.0.1";
const API_BASE = `http://${API_HOST}:${API_PORT}`;
const DB_HOST = API_HOST;
const DB_PORT = 6379;

let mainWindow = null;
let uvicornProcess = null;
let dockerStartedByUs = false;
let bootFailed = false;
const logBuffer = [];
const MAX_LOG_LINES = 800;

function logLine(tag, msg) {
  const line = `[${new Date().toISOString().slice(11, 19)}] [${tag}] ${msg}`;
  logBuffer.push(line);
  if (logBuffer.length > MAX_LOG_LINES) logBuffer.shift();
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send("hallway:log", line);
  }
  // Mirror to file once data dir is known
  try {
    const f = path.join(app.getPath("userData"), "hallway.log");
    fs.appendFileSync(f, line + "\n");
  } catch (_) {}
}

function sendStatus(step, status, detail) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send("hallway:status", { step, status, detail });
  }
}

// --- Paths ---
function backendDir() {
  if (IS_PACKAGED) return path.join(process.resourcesPath, "backend");
  return path.resolve(__dirname, "..");
}
function dataDir() { return app.getPath("userData"); }
function venvDir() { return path.join(dataDir(), "venv"); }
function venvPython() {
  const py = process.platform === "win32" ? "python.exe" : "python";
  return path.join(venvDir(), process.platform === "win32" ? "Scripts" : "bin", py);
}
function venvExists() { return fs.existsSync(venvPython()); }
function userEnvPath() { return path.join(dataDir(), ".env"); }

// --- Small helpers ---
function execFileAsync(file, args, opts = {}) {
  return new Promise((resolve, reject) => {
    execFile(file, args, { timeout: opts.timeout || 120000, ...opts }, (err, stdout, stderr) => {
      if (err) {
        const e = new Error(stderr || stdout || err.message);
        e.stdout = stdout; e.stderr = stderr; e.code = err.code;
        reject(e);
      } else resolve({ stdout: stdout || "", stderr: stderr || "" });
    });
  });
}

function httpGet(url, timeout = 4000) {
  return new Promise((resolve, reject) => {
    const req = http.get(url, { timeout }, (res) => {
      let body = "";
      res.on("data", (c) => (body += c));
      res.on("end", () => resolve({ status: res.statusCode, body }));
    });
    req.on("error", reject);
    req.on("timeout", () => { req.destroy(new Error("timeout")); });
  });
}

async function waitFor(fn, timeoutMs, interval = 600, label = "service") {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try { if (await fn()) return true; } catch (_) {}
    await new Promise((r) => setTimeout(r, interval));
  }
  throw new Error(`${label} did not come up within ${Math.round(timeoutMs / 1000)}s`);
}

function findPython() {
  const candidates = process.platform === "win32"
    ? ["python3.12", "python3.11", "python", "python3"]
    : ["python3.12", "python3.11", "python3", "python"];
  for (const c of candidates) {
    try {
      const out = require("child_process").execFileSync(c, ["--version"], { encoding: "utf8", timeout: 5000 });
      if (/3\.(1[1-9]|[2-9][0-9])\./.test(out)) return c;
      if (!globalThis.__fallbackPy) globalThis.__fallbackPy = c;
    } catch (_) {}
  }
  return globalThis.__fallbackPy || "python3";
}

// --- Boot steps ---
async function ensureEnvFile() {
  const dst = userEnvPath();
  if (fs.existsSync(dst)) return dst;
  const src = path.join(backendDir(), ".env.example");
  try {
    await fs.promises.copyFile(src, dst);
    logLine("env", `.env created at ${dst}`);
  } catch (_) {
    await fs.promises.writeFile(dst, "FALKORDB_URL=redis://localhost:6379\nHALLWAY_GRAPH=hallway\n");
  }
  return dst;
}

async function ensureVenv() {
  if (venvExists()) {
    logLine("venv", "venv already present, skipping creation");
    return venvPython();
  }
  const py = findPython();
  logLine("venv", `creating venv with ${py} at ${venvDir()}`);
  await fs.promises.mkdir(dataDir(), { recursive: true });
  await execFileAsync(py, ["-m", "venv", venvDir()], { timeout: 180000 });
  const pip = process.platform === "win32"
    ? path.join(venvDir(), "Scripts", "pip.exe")
    : path.join(venvDir(), "bin", "pip");
  const req = path.join(backendDir(), "requirements.txt");
  logLine("venv", "installing requirements (first launch takes a minute)…");
  await execFileAsync(pip, ["install", "--upgrade", "pip"], { timeout: 180000 });
  await execFileAsync(pip, ["install", "-r", req], { timeout: 300000 });
  logLine("venv", "venv ready");
  return venvPython();
}

async function dbReachable() {
  return new Promise((resolve) => {
    const net = require("net");
    const s = net.createConnection({ host: DB_HOST, port: DB_PORT, timeout: 2000 });
    s.on("connect", () => { s.end(); resolve(true); });
    s.on("error", () => resolve(false));
    s.on("timeout", () => { s.destroy(); resolve(false); });
  });
}

async function ensureDocker() {
  try {
    await execFileAsync("docker", ["--version"], { timeout: 15000 });
  } catch (_) {
    const err = new Error(
      "Docker isn’t installed or isn’t in PATH. Hallway’s graph database (FalkorDB) runs in Docker.\n\n" +
      "Install Docker Desktop (docker.com/products/docker-desktop) or Colima (brew install colima), then click Retry."
    );
    err.code = "docker_missing";
    throw err;
  }
  try {
    await execFileAsync("docker", ["info"], { timeout: 20000 });
  } catch (_) {
    const err = new Error(
      "Docker is installed but the daemon isn’t running.\n\n" +
      "Open Docker Desktop (or run `colima start`), wait for it to say “Docker is running”, then click Retry."
    );
    err.code = "docker_not_running";
    throw err;
  }
  if (await dbReachable()) {
    logLine("docker", "FalkorDB already reachable on 6379");
    return;
  }
  const composeFile = path.join(backendDir(), "docker-compose.yml");
  logLine("docker", `docker compose up -d (${composeFile})`);
  try {
    await execFileAsync("docker", ["compose", "-f", composeFile, "up", "-d"], { timeout: 120000, cwd: backendDir() });
  } catch (e) {
    logLine("docker", `compose up failed: ${e.message.slice(0, 400)}`);
    throw e;
  }
  dockerStartedByUs = true;
  await waitFor(dbReachable, 90000, 1000, "FalkorDB");
  logLine("docker", "FalkorDB is up");
}

async function ensureSeed(python) {
  // Seed only when the graph is empty, so user edits survive restarts.
  const checkScript = [
    "import os",
    "from graph import seed as s",
    "g = s.connect()",
    "n = g.query('MATCH (p:Person) RETURN count(p)').result_set[0][0]",
    "print(n)",
  ].join("\n");
  const env = {
    ...process.env,
    FALKORDB_URL: process.env.FALKORDB_URL || "redis://localhost:6379",
  };
  // Seed module reads .env from backend dir; also honour userData .env for keys.
  env.PYTHONPATH = backendDir();
  const { stdout } = await execFileAsync(python, ["-c", checkScript], { timeout: 30000, cwd: backendDir(), env });
  const count = parseInt((stdout || "").trim().split(/\s+/).pop(), 10);
  if (Number.isFinite(count) && count > 0) {
    logLine("seed", `graph has ${count} people, skipping seed`);
    return;
  }
  logLine("seed", "empty graph, seeding sample conference…");
  await execFileAsync(python, ["-m", "graph.seed"], { timeout: 60000, cwd: backendDir(), env });
  await execFileAsync(python, ["-c", "from graph import seed as s; from agents import planner; g=s.connect(); planner.build_plan(g,'rene')"],
    { timeout: 60000, cwd: backendDir(), env });
  logLine("seed", "sample conference seeded, plan built for rene");
}

async function startApi(python) {
  if (uvicornProcess && !uvicornProcess.killed) return;
  const args = ["-m", "uvicorn", "app.main:app", "--host", API_HOST, "--port", String(API_PORT)];
  logLine("api", `starting uvicorn on ${API_BASE}`);
  const child = spawn(python, args, {
    cwd: backendDir(),
    env: {
      ...process.env,
      FALKORDB_URL: process.env.FALKORDB_URL || "redis://localhost:6379",
      PYTHONUNBUFFERED: "1",
    },
    windowsHide: true,
  });
  uvicornProcess = child;
  child.stdout.on("data", (d) => logLine("api", String(d).trim().split("\n").pop()));
  child.stderr.on("data", (d) => logLine("api", String(d).trim().split("\n").pop()));
  child.on("exit", (code) => {
    logLine("api", `uvicorn exited (${code})`);
    if (mainWindow && !mainWindow.isDestroyed() && !app.isQuiting) {
      sendStatus("api", "error", `The board stopped (code ${code}). Try Restart from the File menu.`);
    }
  });
  await waitFor(async () => {
    try { const r = await httpGet(`${API_BASE}/api/health`, 2500); return r.status === 200; } catch (_) { return false; }
  }, 60000, 700, "Hallway API");
  logLine("api", "API healthy");
}

async function boot() {
  bootFailed = false;
  const steps = [
    ["env", "Preparing your settings…", async () => { await ensureEnvFile(); }],
    ["python", "Checking Python…", async () => {}],
    ["venv", "Preparing the app (first launch takes a minute)…", async () => { await ensureVenv(); }],
    ["docker", "Starting the graph database…", async () => { await ensureDocker(); }],
    ["seed", "Loading the sample conference…", async () => { await ensureSeed(venvPython()); }],
    ["api", "Starting Hallway…", async () => { await startApi(venvPython()); }],
  ];
  try {
    for (const [id, label, fn] of steps) {
      sendStatus(id, "active", label);
      await fn();
      sendStatus(id, "done", label);
    }
    sendStatus("ready", "done", "Ready");
    if (mainWindow && !mainWindow.isDestroyed()) {
      await mainWindow.loadURL(API_BASE);
    }
  } catch (err) {
    bootFailed = true;
    logLine("boot", `failed: ${err.message}`);
    sendStatus("error", "error", err.message);
    // Also show in window if still on splash
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send("hallway:error", { message: err.message, log: logBuffer.slice(-40).join("\n") });
    }
  }
}

async function stopApi() {
  if (uvicornProcess && !uvicornProcess.killed) {
    try { uvicornProcess.kill("SIGTERM"); } catch (_) {}
    await new Promise((r) => setTimeout(r, 800));
    try { if (!uvicornProcess.killed) uvicornProcess.kill("SIGKILL"); } catch (_) {}
    uvicornProcess = null;
  }
}

// --- Window & app lifecycle ---
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1240,
    height: 840,
    minWidth: 860,
    minHeight: 600,
    show: false,
    backgroundColor: "#fbf6ef",
    title: "Hallway",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  mainWindow.once("ready-to-show", () => mainWindow.show());
  mainWindow.on("closed", () => { mainWindow = null; });
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });
  mainWindow.loadFile(path.join(__dirname, "renderer", "loading.html"));
}

function buildMenu() {
  const isMac = process.platform === "darwin";
  const template = [
    ...(isMac ? [{ role: "appMenu" }] : []),
    {
      label: "File",
      submenu: [
        {
          label: "Restart Hallway",
          accelerator: "CmdOrCtrl+R",
          click: async () => {
            await stopApi();
            if (mainWindow) {
              await mainWindow.loadFile(path.join(__dirname, "renderer", "loading.html"));
            }
            boot();
          },
        },
        {
          label: "Open Board in Browser",
          click: () => shell.openExternal(API_BASE),
        },
        { type: "separator" },
        { role: "quit" },
      ],
    },
    {
      label: "View",
      submenu: [
        { role: "reload" },
        { role: "togglefullscreen" },
        { type: "separator" },
        {
          label: "Show Logs",
          click: () => {
            const dir = dataDir();
            shell.openPath(path.join(dir, "hallway.log"));
          },
        },
      ],
    },
    {
      label: "Help",
      submenu: [
        {
          label: "About Hallway",
          click: () => dialog.showMessageBox({
            type: "info",
            title: "Hallway",
            message: "Hallway",
            detail: "Your conference, run by agents that share one graph.\nEvery suggestion comes with its path: the reason you can audit.",
          }),
        },
        {
          label: "What Hallway needs",
          click: () => dialog.showMessageBox({
            type: "info",
            title: "What Hallway needs",
            message: "Hallway needs Docker running",
            detail: "The graph database (FalkorDB) runs in a small Docker container. Keep Docker Desktop (or Colima) running while you use Hallway. Everything else starts itself.",
          }),
        },
      ],
    },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on("second-instance", () => {
    if (mainWindow) { if (mainWindow.isMinimized()) mainWindow.restore(); mainWindow.focus(); }
  });

  app.whenReady().then(async () => {
    buildMenu();
    createWindow();
    boot();
    app.on("activate", () => {
      if (BrowserWindow.getAllWindows().length === 0) { createWindow(); if (!bootFailed) boot(); }
    });
  });

  ipcMain.on("hallway:retry", async () => {
    if (mainWindow) await mainWindow.loadFile(path.join(__dirname, "renderer", "loading.html"));
    boot();
  });
  ipcMain.handle("hallway:open-logs", async () => {
    const f = path.join(dataDir(), "hallway.log");
    await fs.promises.mkdir(dataDir(), { recursive: true });
    if (!fs.existsSync(f)) await fs.promises.writeFile(f, logBuffer.join("\n") + "\n");
    shell.openPath(f);
    return f;
  });
  ipcMain.handle("hallway:open-external", async (_e, url) => { shell.openExternal(url); });

  app.on("window-all-closed", async () => {
    await stopApi();
    if (process.platform !== "darwin") app.quit();
  });

  app.on("before-quit", async () => {
    app.isQuiting = true;
    await stopApi();
  });
}
