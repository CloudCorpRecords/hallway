"use strict";
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("hallway", {
  onStatus: (fn) => ipcRenderer.on("hallway:status", (_e, data) => fn(data)),
  onLog: (fn) => ipcRenderer.on("hallway:log", (_e, line) => fn(line)),
  onError: (fn) => ipcRenderer.on("hallway:error", (_e, data) => fn(data)),
  retry: () => ipcRenderer.send("hallway:retry"),
  openLogs: () => ipcRenderer.invoke("hallway:open-logs"),
  openExternal: (url) => ipcRenderer.invoke("hallway:open-external", url),
});
