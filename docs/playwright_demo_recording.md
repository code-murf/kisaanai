# Playwright Demo Recording

## What this gives you

- Separate demo clips for each main product function
- A repeatable browser flow for recording product demos
- A simple fallback when Playwright MCP is not mounted in the current client session
- A presenter-ready order for showing each feature in a live demo

Output folder:

- `ui-videos/function-demos`

Recorder script:

- [record-feature-demos.js](C:\Users\Asus\Desktop\Aiforbharat\record-feature-demos.js)

Generated clips:

1. `ui-videos/function-demos/01-home-dashboard.mp4`
2. `ui-videos/function-demos/02-voice-assistant.mp4`
3. `ui-videos/function-demos/03-price-charts.mp4`
4. `ui-videos/function-demos/04-crop-doctor.mp4`
5. `ui-videos/function-demos/05-mandi-finder.mp4`
6. `ui-videos/function-demos/06-news-alerts.mp4`
7. `ui-videos/function-demos/07-settings.mp4`

## Playwright MCP workflow

If your client has Playwright MCP installed, the browser flow is:

1. `browser_navigate` to the route you want to demo
2. `browser_snapshot` to get stable element refs
3. `browser_click`, `browser_type`, or `browser_file_upload` to perform the interaction
4. `browser_wait_for` to let content settle
5. `browser_take_screenshot` for stills

Typical sequence per function:

1. Home: navigate, scroll, screenshot
2. Voice: navigate, click example query, wait for answer
3. Charts: navigate, switch tabs between history, forecast, comparison
4. Doctor: upload crop image, click diagnose, wait for result
5. Mandi: search or sort, pause on best result
6. News: scroll through cards
7. Settings: switch language, scroll settings

## Local fallback in this repo

This repo already has Playwright installed under `kisaanai-video/node_modules`, so you can record the same demo flow without MCP:

1. Make sure `frontend/.next` exists
2. Run:

```powershell
node record-feature-demos.js
```

What the script does:

1. Starts the frontend on `http://127.0.0.1:3000` if it is not already running
2. Proxies API calls to `API_PROXY_TARGET` or `https://kisaanai-backend.onrender.com`
3. Records a separate browser video for each feature
4. Converts each clip to MP4 when `ffmpeg` is available
5. Writes a manifest to `ui-videos/function-demos/manifest.json`

## Demo order

Use these clips in this order:

1. `01-home-dashboard`
2. `02-voice-assistant`
3. `03-price-charts`
4. `04-crop-doctor`
5. `05-mandi-finder`
6. `06-news-alerts`
7. `07-settings`

## What each clip shows

1. Home Dashboard
   - Opens the main dashboard
   - Scrolls through the product overview
   - Use this to establish that all key tools are available from one place
2. Voice Assistant
   - Opens the voice page in mobile view
   - Clicks an example farmer query
   - Pauses while the answer renders
3. Price Charts
   - Opens charts
   - Switches between history, forecast, and mandi comparison
   - Shows that the user can move from raw prices to decision support
4. Crop Doctor
   - Uploads a crop image
   - Runs diagnosis
   - Waits on the result state
5. Mandi Finder
   - Opens mandi search
   - Sorts by best price and nearest
   - Types a mandi search term
6. News Alerts
   - Opens the news feed
   - Scrolls through current cards
   - Shows advisory and update coverage
7. Settings
   - Opens settings in mobile view
   - Switches language
   - Scrolls through user controls

## Demo talk track

Use one short line per clip:

1. Home Dashboard: `This is the operational home screen where the farmer sees prices, advisories, and tools in one place.`
2. Voice Assistant: `A farmer can ask in natural language and get an immediate answer without navigating complex screens.`
3. Price Charts: `This view moves from market history to forecast so the farmer can decide when to sell.`
4. Crop Doctor: `The farmer uploads a crop photo and gets an instant diagnosis workflow.`
5. Mandi Finder: `This compares mandi options so the farmer can choose the better selling point.`
6. News Alerts: `Important market and farming updates are surfaced as a feed instead of being missed.`
7. Settings: `Language and personal preferences stay simple, so the product remains usable for real farmers.`

## Demo tips

1. Keep each clip between 6 and 12 seconds
2. Show one clear action per clip
3. Use the voice clip early because it explains the product fastest
4. Use charts, doctor, and mandi as proof of utility
5. End with settings or return to home before stitching the final demo

## Crop Doctor input

The recorder looks for one of these files automatically:

1. `presentation_assets/screenshots/crop-doctor-real-api.png`
2. `kisaanai-video/assets/crop-doctor.png`
3. `kisaanai-video/assets/crop-doctor-results.png`

Replace that with a real crop photo if you want a cleaner diagnosis demo.
