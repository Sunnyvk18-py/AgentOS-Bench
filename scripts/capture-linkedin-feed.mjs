import { chromium } from "playwright";
import { mkdirSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const outDir = join(root, "assets");
mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 1200, height: 627 },
  deviceScaleFactor: 2,
});

await page.goto("http://127.0.0.1:3000/", { waitUntil: "networkidle", timeout: 60000 });
await page.waitForTimeout(3000);

await page.screenshot({
  path: join(outDir, "agentos-bench-dashboard-linkedin-feed.png"),
});

await browser.close();
console.log("Saved LinkedIn feed image (1200x627)");
