# GameStats — Roblox Analytics Dashboard

A responsive GitHub Pages dashboard for Roblox experience **Click For Free**.

- Universe ID: `4614743437`
- Place ID: `13234175149`
- Public stats: live CCU, visits, favorites, likes/dislikes
- Collected history: CCU samples (up to 7 days)
- Private analytics (optional): daily revenue, DAU, D1/D7/D30 retention
- Optional Discord alerts at 50, 75, and 100 CCU
- Designed for phones, tablets, and desktop browsers

## Setup (iPad-friendly)

### 1. Enable GitHub Pages

In this repository, open **Settings → Pages**. Under **Build and deployment**, set **Source** to **GitHub Actions**.

### 2. Add Roblox analytics access (optional, for revenue / DAU / retention)

In Roblox Creator Dashboard, create an Open Cloud API key for this experience. Grant the key the `universe.analytics:read` permission for the universe analytics system.

In GitHub, open **Settings → Secrets and variables → Actions → New repository secret**:

- Name: `ROBLOX_API_KEY`
- Value: your Roblox API key

Do not put this key in `index.html`, `app.js`, or any public file. The collector runs on GitHub's servers and reads it from the Actions secret.

If you skip this step, public statistics and CCU history still work.

### 3. Add Discord alerts (optional)

Create a Discord webhook in the channel where alerts should appear. Add another repository Actions secret:

- Name: `DISCORD_WEBHOOK_URL`
- Value: the webhook URL

Keep the webhook URL private. Without this secret, the dashboard still collects statistics; it simply won't send Discord messages.

### 4. Run the first collection

Open **Actions → GameStats collector and deploy → Run workflow**. The first scheduled run also starts automatically, typically within a few minutes.

### 5. Open the dashboard

After the workflow succeeds, visit:

https://scriptedlantern.github.io/game-stats/

GitHub Pages may take a few minutes to publish the first deployment.

## Data notes

- Public statistics are read from Roblox's public game endpoints.
- CCU history starts when the collector first runs; it cannot reconstruct earlier CCU.
- The collector samples every five minutes when GitHub Actions runs on schedule. GitHub may delay scheduled jobs during busy periods.
- Revenue, DAU, and retention require a Roblox API key with analytics read permission and creator analytics access to this experience.
- Analytics are refreshed once per UTC day. Roblox may return incomplete values for the newest date or for retention cohorts that have not matured yet.
- This is a creator-facing dashboard. Do not expose private API keys or Discord webhook URLs in the website.

## Local preview

Open `index.html` in a browser. The initial page displays placeholders until `data.json` has been populated by the collector.
