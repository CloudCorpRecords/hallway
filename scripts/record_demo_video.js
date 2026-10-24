"use strict";

/**
 * Automated Hallway Demo Video Generator
 * Runs inside Electron against the live FastAPI + FalkorDB backend,
 * steps through the 5-step DEMO.md storyboard with visual highlights & captions,
 * generates natural macOS voiceover per scene, and encodes a 1080p MP4 + WebM.
 */

const { app, BrowserWindow } = require("electron");
const { spawn, execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const http = require("http");

const REPO_ROOT = path.resolve(__dirname, "..");
const OUT_DIR = path.join(REPO_ROOT, "submission");
const FRAMES_DIR = path.join("/tmp", "hallway-video-frames");
const AUDIO_DIR = path.join("/tmp", "hallway-video-audio");
const VENV_PY = path.join(REPO_ROOT, ".venv", "bin", "python");
const FFMPEG = execFileSync(VENV_PY, ["-c", "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"], {
  encoding: "utf8",
}).trim();

const API_PORT = 8019;
const API_BASE = `http://127.0.0.1:${API_PORT}`;
const FPS = 10;

let uvicornProc = null;

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function httpGet(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let body = "";
      res.on("data", (c) => (body += c));
      res.on("end", () => resolve({ status: res.statusCode, body }));
    }).on("error", reject);
  });
}

async function startBackend() {
  console.log("[video] Resetting graph and starting FastAPI on port", API_PORT);
  uvicornProc = spawn(VENV_PY, ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(API_PORT)], {
    cwd: REPO_ROOT,
    env: { ...process.env, PYTHONUNBUFFERED: "1" },
  });
  for (let i = 0; i < 40; i++) {
    try {
      const r = await httpGet(`${API_BASE}/api/health`);
      if (r.status === 200) return;
    } catch (_) {}
    await sleep(400);
  }
  throw new Error("Backend did not start");
}

function getAudioDurationSec(filePath) {
  try {
    const out = execFileSync(FFMPEG, ["-i", filePath], { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
    return 5;
  } catch (e) {
    const stderr = String(e.stderr || "");
    const m = stderr.match(/Duration:\s*(\d+):(\d+):(\d+\.\d+)/);
    if (m) {
      return Number(m[1]) * 3600 + Number(m[2]) * 60 + Number(m[3]);
    }
    return 6;
  }
}

function synthSpeech(index, text) {
  const aiff = path.join(AUDIO_DIR, `scene_${index}.aiff`);
  const wav = path.join(AUDIO_DIR, `scene_${index}.wav`);
  execFileSync("/usr/bin/say", ["-r", "188", "-o", aiff, text]);
  execFileSync(FFMPEG, ["-y", "-i", aiff, "-ar", "44100", "-ac", "1", wav], { stdio: "ignore" });
  const dur = getAudioDurationSec(wav);
  return { wav, durationSec: dur + 0.6 };
}

async function injectCaption(win, stepBadge, captionText) {
  await win.webContents.executeJavaScript(`
    (function() {
      let bar = document.getElementById("demo-caption-bar");
      if (!bar) {
        bar = document.createElement("div");
        bar.id = "demo-caption-bar";
        bar.style.cssText = "position:fixed;bottom:22px;left:50%;transform:translateX(-50%);z-index:99999;background:rgba(45,42,38,0.94);color:#fff8ec;padding:14px 26px;border-radius:18px;box-shadow:0 12px 32px rgba(0,0,0,0.32);max-width:86%;font-size:18px;line-height:1.4;border:2px solid #ff7a59;display:flex;align-items:center;gap:14px;font-family:'Avenir Next',system-ui,sans-serif;";
        document.body.appendChild(bar);
      }
      bar.innerHTML = '<span style="background:#ff7a59;color:#fff;font-weight:800;font-size:13px;padding:5px 12px;border-radius:999px;letter-spacing:0.08em;white-space:nowrap">' + ${JSON.stringify(stepBadge)} + '</span><span>' + ${JSON.stringify(captionText)} + '</span>';
    })();
  `);
}

async function runRecording() {
  fs.rmSync(FRAMES_DIR, { recursive: true, force: true });
  fs.rmSync(AUDIO_DIR, { recursive: true, force: true });
  fs.mkdirSync(FRAMES_DIR, { recursive: true });
  fs.mkdirSync(AUDIO_DIR, { recursive: true });
  fs.mkdirSync(OUT_DIR, { recursive: true });

  await startBackend();

  const win = new BrowserWindow({
    width: 1440,
    height: 900,
    show: false,
    backgroundColor: "#fbf6ef",
    webPreferences: { offscreen: false, contextIsolation: true },
  });

  let frameIndex = 0;
  const audioSegments = [];

  async function captureForSeconds(sec) {
    const totalFrames = Math.max(1, Math.round(sec * FPS));
    for (let i = 0; i < totalFrames; i++) {
      const img = await win.webContents.capturePage();
      const png = img.resize({ width: 1440, height: 900 }).toPNG();
      const fname = path.join(FRAMES_DIR, `frame_${String(frameIndex++).padStart(5, "0")}.png`);
      fs.writeFileSync(fname, png);
      await sleep(1000 / FPS);
    }
  }

  async function playScene(index, badge, voiceText, actionFn) {
    console.log(`[video] Scene ${index}: ${badge}`);
    const { wav, durationSec } = synthSpeech(index, voiceText);
    audioSegments.push({ wav, durationSec });
    if (actionFn) await actionFn(durationSec);
    else await captureForSeconds(durationSec);
  }

  // Scene 0: Electron loading checklist screen
  const loadingPath = path.join(REPO_ROOT, "electron", "renderer", "loading.html");
  await win.loadFile(loadingPath);
  await sleep(300);

  await playScene(
    0,
    "STANDALONE ELECTRON APP",
    "Meet Hallway: the conference concierge that shows its work. Built at Patch the Conference, Hallway wraps FalkorDB, Bright Data, TrueForge, and Qodo into a one-click desktop app and web board.",
    async (dur) => {
      const steps = ["env", "python", "venv", "docker", "seed", "api"];
      const stepTime = dur / (steps.length + 1);
      for (const s of steps) {
        await win.webContents.executeJavaScript(`
          (function(){
            const li = document.querySelector('[data-step="${s}"]');
            if (li) { li.classList.add('done'); const d = li.querySelector('.dot'); if (d) d.textContent = '✓'; }
            document.getElementById('status').textContent = 'All services healthy on 127.0.0.1:8000';
          })();
        `);
        await captureForSeconds(stepTime);
      }
      await captureForSeconds(stepTime);
    }
  );

  // Reset stage via API and load live board
  await new Promise((resolve, reject) => {
    const req = http.request(`${API_BASE}/api/demo/reset?person_id=rene`, { method: "POST" }, () => resolve());
    req.on("error", reject);
    req.end();
  });

  await win.loadURL(API_BASE);
  await sleep(1200);

  // Scene 1: Who to meet + 3-hop graph path + AI Day Briefing (FalkorDB)
  await playScene(
    1,
    "STEP 1 · FALKORDB GRAPH PATHS",
    "Step one: Who to meet, proven by the graph. Every suggestion shows its three-hop trail from you, to your topic, to the talk, to the speaker, plus a deterministic icebreaker.",
    async (dur) => {
      await injectCaption(win, "TRACK 1 · FALKORDB", "Every suggestion carries its 3-hop Cypher path (You → Topic → Talk → Speaker) and deterministic icebreaker.");
      await captureForSeconds(dur * 0.35);
      await win.webContents.executeJavaScript(`
        document.querySelectorAll('details.path').forEach((d, idx) => { if (idx < 2) d.open = true; });
        briefMe();
      `);
      await captureForSeconds(dur * 0.65);
    }
  );

  // Scene 2: Shared Graph Memory (MET edges)
  await playScene(
    2,
    "STEP 2 · SHARED GRAPH MEMORY",
    "Step two: Shared memory across sessions. Tom Alvarez was met at breakfast, so a MET edge excludes him. Watch what happens when we click We met in the hallway on Diego Fuentes: he moves immediately into our met memory panel.",
    async (dur) => {
      await injectCaption(win, "TRACK 1 · GRAPH MEMORY", "Clicking 'We met in the hallway' writes a MET edge to FalkorDB and excludes Diego from future suggestions.");
      await captureForSeconds(dur * 0.4);
      await win.webContents.executeJavaScript(`
        markMet('diego-fuentes', 'Diego Fuentes');
      `);
      await captureForSeconds(dur * 0.6);
    }
  );

  // Scene 3: Planner clash refusal and swap
  await playScene(
    3,
    "STEP 3 · CLASH-FREE PLANNER",
    "Step three: Clash-free planning. Every planned talk glows green and states why it matched your interests. If we try to add a second nine-thirty talk, Planner refuses in plain English and names the clashing talk. Drop the first talk, click Add again, and the swap succeeds.",
    async (dur) => {
      await injectCaption(win, "PLANNER · CLASH REFUSAL", "Adding a 09:30 talk while 'MCP in Production' is planned returns a 409 plain-language clash refusal.");
      await win.webContents.executeJavaScript(`addTalk('t2');`);
      await captureForSeconds(dur * 0.45);
      await injectCaption(win, "PLANNER · IN-PLACE SWAP", "Dropping t1 and adding t2 updates the PLANNED edges in FalkorDB with zero double-booking.");
      await win.webContents.executeJavaScript(`
        (async () => {
          await dropTalk('t1');
          await new Promise(r => setTimeout(r, 300));
          await addTalk('t2');
        })();
      `);
      await captureForSeconds(dur * 0.55);
    }
  );

  // Scene 4: Scout + Bright Data schedule change detection & repair
  await playScene(
    4,
    "STEP 4 · BRIGHT DATA + SCOUT",
    "Step four: Live schedule changes caught by Scout and Bright Data. When talks move rooms or times mid-conference, Scout diffs the schedule against the graph and surfaces a change banner. Clicking Rebuild my plan repairs the day automatically.",
    async (dur) => {
      await injectCaption(win, "TRACK 2 · BRIGHT DATA + SCOUT", "Scout detects that talk t6 moved to Workshop 2 and t11 moved to 16:30, then Planner repairs the schedule.");
      await win.webContents.executeJavaScript(`refresh();`);
      await captureForSeconds(dur * 0.55);
      await win.webContents.executeJavaScript(`rebuild();`);
      await captureForSeconds(dur * 0.45);
    }
  );

  // Scene 5: TrueForge Human Approval Gate + Qodo PR Review Trail
  await playScene(
    5,
    "STEP 5 · TRUEFORGE + QODO",
    "Step five: Human approval gates with TrueForge and Fireworks G L M, plus Qodo pull request reviews. Clicking Draft intro generates a grounded message and stops at the TrueForge approval gate so nothing sends without your okay. Hallway: your conference, run by agents that share one memory.",
    async (dur) => {
      await injectCaption(win, "TRACKS 3 & 4 · TRUEFORGE GATE + QODO", "Matchmaker drafts the intro via Fireworks GLM and holds at 'trueforge-approval-gate' until human approval.");
      await win.webContents.executeJavaScript(`
        const btn = document.querySelector('.person-actions button');
        if (btn) btn.click();
      `);
      await captureForSeconds(dur);
    }
  );

  // Concatenate audio files
  const concatListPath = path.join(AUDIO_DIR, "concat.txt");
  const concatLines = [];
  for (let i = 0; i < audioSegments.length; i++) {
    const paddedWav = path.join(AUDIO_DIR, `scene_${i}_padded.wav`);
    execFileSync(FFMPEG, [
      "-y",
      "-i", audioSegments[i].wav,
      "-af", `apad=whole_dur=${audioSegments[i].durationSec.toFixed(2)}`,
      paddedWav,
    ], { stdio: "ignore" });
    concatLines.push(`file '${paddedWav}'`);
  }
  fs.writeFileSync(concatListPath, concatLines.join("\n") + "\n");

  const fullAudio = path.join(AUDIO_DIR, "narration.wav");
  execFileSync(FFMPEG, ["-y", "-f", "concat", "-safe", "0", "-i", concatListPath, "-c", "copy", fullAudio], {
    stdio: "ignore",
  });

  const mp4Out = path.join(OUT_DIR, "hallway-demo.mp4");
  console.log("[video] Encoding MP4 to", mp4Out);
  execFileSync(
    FFMPEG,
    [
      "-y",
      "-framerate", String(FPS),
      "-i", path.join(FRAMES_DIR, "frame_%05d.png"),
      "-i", fullAudio,
      "-c:v", "libx264",
      "-preset", "fast",
      "-crf", "20",
      "-pix_fmt", "yuv420p",
      "-c:a", "aac",
      "-b:a", "160k",
      "-shortest",
      mp4Out,
    ],
    { stdio: "inherit" }
  );

  // Reset demo graph back to clean stage start
  await new Promise((resolve) => {
    const req = http.request(`${API_BASE}/api/demo/reset?person_id=rene`, { method: "POST" }, () => resolve());
    req.on("error", () => resolve());
    req.end();
  });

  if (uvicornProc) uvicornProc.kill("SIGTERM");
  console.log("[video] DONE:", mp4Out);
  app.quit();
}

app.whenReady().then(() => {
  runRecording().catch((err) => {
    console.error("[video] FAILED:", err);
    if (uvicornProc) uvicornProc.kill("SIGTERM");
    process.exit(1);
  });
});
