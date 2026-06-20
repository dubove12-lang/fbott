# FatBot Copytrading Full MVP – Wide UI v2

Updated full MVP version with:
- full-width layout
- styling closer to FatBot Perps / dashboard look
- reduced emoji usage
- cleaner icon/badge system
- left Smart Traders / center My Copy Wallets / right Live Positions layout
- trader profile popup modal

## Run

```powershell
cd C:\path\to\fatbot-copytrading-full-mvp-wide-v2
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```


## v4 change
- Top navigation label text increased by 10px: 9px -> 19px.
- Dock item size and topbar height adjusted so labels fit cleanly.


## v5 change
- Top navigation icons stay at 22px.
- Top navigation text reduced by 7px: 19px -> 12px.


## v6 layout update
- Removed Pool Copy panel from left column for now.
- Expanded Smart Traders panel to fill the left side down to the bottom.
- Moved PnL Allocation panel to the top of the center column.


## v7 fix
- Fixed frontend loading issue after removing Pool Copy panel.
- app.js no longer crashes when createPoolBtn or poolList is not present.

## v8 Hydromancer leaderboard

Smart Traders can now be loaded automatically from Hydromancer `userPnlLeaderboard`.

### Setup

Create `.env` or set environment variables before running:

```powershell
$env:HYDROMANCER_API_KEY="YOUR_KEY"
$env:HYDROMANCER_LEADERBOARD_WINDOW="30d"
$env:HYDROMANCER_LEADERBOARD_SORT_BY="totalPnl"
$env:HYDROMANCER_LEADERBOARD_LIMIT="50"
```

Then run:

```powershell
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### Current logic

- If `HYDROMANCER_API_KEY` exists, `/api/traders` calls Hydromancer.
- If it is missing or the API call fails, the app falls back to SQLite mock seed data.
- This version is intentionally PnL-led only.
- Later, replace ranking with FatBot Copy Score using our own scoring layer.


## v9 UI update
- Left panel is now full-height PnL Leaderboard.
- Added tabs: Global Leaderboard / Favourite / Copied Wallets.
- Added favourite star per trader using browser localStorage.
- Center My Copy Wallets replaced with Single Copytrading and Multi Copytrading.
- Empty Single/Multi sections show full-row start buttons.
- Target vs Actual panel removed.
- Frontend enforces max 5 single copy wallets and shows 0/5, 0/2 counters.


## v10 fix
- Added cache-busting for CSS/JS.
- Fixed possible `classList is null` frontend error with null-safe DOM access.
- Strengthened leaderboard tab styling.


## v11 UI update
- Single Copytrading now always shows 5 fixed slots.
- Multi Copytrading now always shows 3 fixed slots.
- Empty slots show a plus button; filled slots show the wallet in the same fixed area.
- Multi limit updated from 2 to 3.


## v12 functional plus buttons
- Empty Single slots now open the settings modal.
- User can select trader from the leaderboard inside the modal.
- Settings are saved and a generated/active wallet is created through the API.
- Empty Multi slots now open a multi settings modal using the top 3 leaderboard traders.


## v13 wallet picker settings
- Multi setup lets user select up to 5 wallets from leaderboard.
- Multi setup includes Add your own wallet.
- Single setup includes Add your own wallet, overriding selected leaderboard wallet.
- Settings now focus on copy multiplier 0.1x-10x, max drawdown %, cross margin info, and max gross exposure.
- Pool API accepts 2-5 wallet addresses.


## v14 right side update
- Right side now has Multi Copytrading Leaderboard and Live Trader Feed.
- Multi leaderboard uses created pool/multi copy wallets sorted by PnL.
- Copy button opens multi settings with the same copied wallet members.
- Live Trader Feed uses current copy wallet position activity for MVP.


## v15 update
- Multi settings now include Vault name.
- Vault name is sent to /api/pools and displayed in Multi Copytrading Leaderboard.
- Live Trader Feed now simulates 50 random trade transactions.
- A new random transaction is inserted every 3 seconds.
- Feed rows include vault name, ticker, USD size and USD PnL.
- Entire feed row is green/red depending on PnL.


## v16 update
- Create Single Wallet now skips funding/generation steps and immediately creates + activates wallet.
- Create Multi Wallet now immediately creates + activates the multi copy wallet.
- Clicking a Single/Multi wallet expands detailed stats and open positions.
- Expanded wallet view includes Close Copytrading.
- After closing, Withdraw Funds form appears with destination wallet and Confirm Withdraw and Delete.
- DELETE /api/wallets/{id} removes wallet/pool data from SQLite.


## v17 fix
- Fixed `state.expandedWallets is undefined` by adding defensive UI state initialization.
- Added cache busting to v17.


## v18 fix
- Fixed `database is locked` on POST /api/pools by creating pool + wallet in one SQLite transaction.
- Multi Copytrading create now works and activates the pool wallet immediately.
- Copy Vault from Multi Copytrading Leaderboard opens the same settings modal flow as normal multi creation.
- Added double-click guard while creating wallets/vaults.


## v19 update
- Copy Vault from Multi Copytrading Leaderboard now uses a single-wallet copy flow.
- Copying a multi vault creates one user copy wallet in the Single Copytrading slots.
- The copied vault is treated as one source wallet (`vault:<pool_id>`), not as a new Multi Copytrading pool.
- Multi Create still creates real multi vaults in the Multi Copytrading slots.
- SQLite busy timeout/WAL added for more robust local testing.


## v20 fix
- Fixed PATCH /api/wallets/{id}/settings crash: `copy_wallet_settings` has `wallet_id` as primary key, not `id`.
- Added defensive fallback: if settings row is missing, it is created before patching.


## v21 fix
- Copy Vault can no longer create more than 5 Single Copytrading wallets.
- Opening Copy Vault now shows an alert when Single slots are full.
- Single direct creation also checks the 5/5 limit before API calls.
- Multi direct creation checks the 3/3 limit before API calls.
- Backend generate_wallet also enforces 5 single / 3 multi limits and returns HTTP 400.


## v22 Hydromancer live leaderboard update
Observed userPnlLeaderboard fields:
- user
- totalPnl
- volumeTraded
- totalTrades
- winRate
- totalFees
- totalFunding
- daysActive
- accountAgeDays
- humanScore
- tradedPairs

Supported windows from the endpoint:
- 1d
- 7d
- 30d
- 90d
- all

Supported sortBy values tested:
- totalPnl
- volume
- winRate

New test endpoint:
- GET /api/hydromancer-check

If HYDROMANCER_API_KEY is set and the live leaderboard fails, the API now returns an error instead of silently showing mock data unless:
HYDROMANCER_ALLOW_MOCK_FALLBACK=true


## v23 Hydromancer UI fix
- Fixed wrong display where absolute PnL was shown as a percentage.
- Hydromancer modal now shows real endpoint fields:
  PnL Window, Volume Traded, Win Rate, Total Trades, Active Days,
  Account Age, Total Fees, Total Funding, Human Score, Traded Pairs.
- Account Value/Open Positions are not shown for Hydromancer rows because userPnlLeaderboard does not return them.
- Leaderboard rows now display PnL as USD, plus Volume and Win Rate where space allows.


## v24 left scroll fix
- Left PnL Leaderboard now has fixed viewport height.
- Trader list scrolls inside the panel instead of overflowing down the page.
- Added styled scrollbar and prevented page horizontal overflow.


## v25 Trader profile cleanup + Hyperliquid live positions
- Removed Source and Rank cards from Trader Profile modal.
- Removed Human Score card from modal because Hydromancer does not document exact formula in the endpoint response.
- Removed traded pairs info row.
- Added public Hyperliquid clearinghouseState enrichment for wallet profile:
  - Account Value
  - Live Positions count
  - Position coin, side, notional, entry, mark, unrealized PnL, liquidation price
- Added backend/app/hyperliquid_client.py.


## v26 Mark price fix
- Hyperliquid clearinghouseState often does not return markPx directly.
- Backend now computes mark price as `positionValue / abs(szi)` when markPx is missing.
- Position rows now also include size and rough pnl_pct.
- Frontend shows `—` instead of `0` if mark/entry still cannot be derived.


## v27 Hyperliquid allMids live price
- Added Hyperliquid Info endpoint:
  - `POST https://api.hyperliquid.xyz/info`
  - payload: `{"type":"allMids"}`
- Trader Profile now uses:
  - `clearinghouseState` for open positions and account state
  - `allMids` for current live price per coin
- Position table now shows:
  - Entry
  - Live Price
  - PnL
  - Liq
  - Source (`allMids` or fallback `clearinghouseState`)
- Backend fallback remains:
  - if `allMids` does not contain the coin, price falls back to `positionValue / abs(szi)`.


## v28 Trader profile cleanup + CoinGecko icons
- Moved `COPY THIS TRADER` button to the top-right of Trader Profile.
- Removed the bottom copy button from the positions header.
- Replaced Account Value card with Volume/Live Positions only.
- Removed the Source column from the positions table.
- Added `backend/app/token_icons.py` with CoinGecko image URL overrides for common tickers.
- Hyperliquid position rows now include `icon_url`, and frontend displays token images when available.
- Unknown or Hyperliquid-only tickers still fall back to the existing colored letter badge.


## v29 Trader profile cleanup
- Removed explanatory note about clearinghouseState/allMids from Trader Profile.
- Removed "Hydromancer PnL leaderboard trader" subtitle from Trader Profile.
- Removed Active Days card from Trader Profile.


## v30 Position side coloring
- Position ticker text is green for Long positions.
- Position ticker text is red for Short positions.
- Applied to Trader Profile live positions and expanded wallet position rows.


## v31 Trader profile stats reorder
- Removed Total Fees card from Trader Profile.
- Added Account Value back to the first row, next to PnL Window.
- Moved Volume to the previous Total Fees position.


## v32 Leaderboard module update
- Leaderboard tabs changed to:
  - Top Traders
  - FatBot Vaults
  - Favourite
  - My Copytrading
- FatBot Vaults uses the same row layout/stat columns as Top Traders.
- Added fixed FatBot vault addresses:
  - 0x0baFb25EF191bFe7A2727E14F5BbfC36610EC62A
  - 0x0baFb25EF191bFe7A2727E14F5BbfC36610EC62A
- Added `/api/fatbot-vaults`.
- Hydromancer/top trader rows show an `HL` logo bubble.
- FatBot Vault rows show a FatBot logo bubble.
- Upload FatBot logo to:
  - `frontend/assets/fatbot-logo.png`
- If the logo file is missing, UI falls back to a yellow `FB` badge.


## v33 Asset logos in leaderboard and Trader Profile
- FatBot Vault rows still use `/static/assets/fatbot-logo.png`.
- Top Traders / Hydromancer rows now use `/static/assets/hyperliquid-logo.png`.
- Trader Profile header now uses the same provider logo:
  - FatBot logo for FatBot Vaults
  - Hyperliquid logo for Top Traders
- If logo files are missing, UI falls back to `FB` / `HL` text badges.

Upload logos here:
- `frontend/assets/fatbot-logo.png`
- `frontend/assets/hyperliquid-logo.png`


## v34 Logo fill update
- Provider logos now fill the whole badge/window.
- Removed inner padding from HL/FatBot logo images.
- Logo image uses object-fit: cover and inherits rounded corners.


## v35 Logo zoom refinement
- Increased provider logo badge size from 42px to 44px.
- Zoomed/cropped HL logo more so it fills the badge better.
- Zoomed FatBot logo slightly so it fills the badge better.
- Applied same behavior in Trader Profile header logos.


## v36 FatBot Vault stats from Hyperliquid endpoints
FatBot Vault profile stats are now composed from public Hyperliquid endpoints:
- `clearinghouseState`:
  - account value
  - live open positions
  - position notional, entry, liquidation, unrealized PnL
- `allMids`:
  - live price per coin
- `userFillsByTime` over last 30 days:
  - 30D closed PnL approximation
  - 30D volume
  - fees
  - fill/trade count
  - win rate based on positive closedPnl fills

FatBot Vaults now use the same Trader Profile live layout as Top Traders.


## v37 FatBot Vaults cleanup
- FatBot Vaults tab now shows only the two fixed platform vault addresses:
  - 0x0baFb25EF191bFe7A2727E14F5BbfC36610EC62A
  - 0x20c4F93BcAd80C7B83c20dEcA8A7bc91B9e6a3b0
- User-created multi copy pools are no longer mixed into the FatBot Vaults leaderboard tab.


## v38 FatBot Vault PnL percent fix
- Fixed FatBot Vault leaderboard PnL percentage calculation.
- Previous display could show raw USD PnL as percent, e.g. `$40` shown as `40%`.
- New formula:
  - `pnl_pct = total_pnl_usd / account_value * 100`
  - Example: `$40 / $1,000 = 4%`
- Backend now returns:
  - `pnl_pct`
  - `pnl_usd`
  - `pnl_display_mode = percent_of_account_value`
- Frontend uses `pnl_pct` for FatBot Vaults and still uses USD PnL for Top Traders.


## v39 Fast FatBot Vaults + 10k fills coverage
- Added short in-memory backend cache for `/api/fatbot-vaults`.
  - Default TTL: `FATBOT_VAULT_CACHE_TTL_SECONDS=60`
  - Opening a vault profile reuses cached data instead of recomputing every click.
- FatBot Vaults no longer call Hydromancer leaderboard inside the vault stats path.
- `userFillsByTime` is now queried in parallel time chunks:
  - default `HYPERLIQUID_FILLS_CHUNKS=5`
  - each response is capped by Hyperliquid at 2,000 fills
  - 5 chunks allow up to 10,000 fills over the 30d window
- Added de-duplication across chunk responses.
- Backend exposes metadata:
  - `fills_chunks`
  - `fills_max_possible`
  - `fills_is_probably_capped`


## v40 Vault funding + account age enrichment
- Added Hyperliquid `userFunding` integration for FatBot Vaults.
  - 30D funding is now summed from `userFunding` instead of showing `—`.
  - Uses parallel 5-chunk fetch similar to fills.
- Added best-effort Account Age for FatBot Vaults.
  - Hyperliquid `clearinghouseState` does not expose simple account-created date.
  - Backend estimates age from earliest available public user activity:
    - `userFillsByTime`
    - `userNonFundingLedgerUpdates`
  - For extremely active wallets, this can be an approximation due to HL history/cap limits.
- New env controls:
  - `HYPERLIQUID_FUNDING_CHUNKS=5`
  - `HYPERLIQUID_FUNDING_WORKERS=5`


## v41 Top navigation FatBot Vaults snapshot
- Added a new top navigation item to the right of Copytrading:
  - `FatBot Vaults`
- It is currently a 1:1 snapshot of the current Copytrading window.
- Clicking `Copytrading` or `FatBot Vaults` only changes the active top-nav highlight.
- Main content stays absolutely identical, as requested.


## v42 Fast profile opening
- Trader/Vault profile modal now opens immediately with a loading state.
- Backend caches Hydromancer Top Traders leaderboard for 60s:
  - `TRADER_LEADERBOARD_CACHE_TTL_SECONDS=60`
- Backend already caches FatBot Vault stats for 60s.
- Hyperliquid `allMids` now has a small 15s cache:
  - `HYPERLIQUID_ALL_MIDS_CACHE_TTL_SECONDS=15`
- This removes most of the 10-20s perceived delay when clicking HL traders or FatBot Vaults.


## v43 Faster profile backend
- Added per-wallet profile cache:
  - `PROFILE_CACHE_TTL_SECONDS=120`
- FatBot Vault profile enrichment now runs independent Hyperliquid calls concurrently:
  - `clearinghouseState`
  - `allMids`
  - `userFillsByTime` chunked stats
  - `userFunding` chunked stats
  - account age best-effort
- This reduces first uncached profile load because fills/funding/age no longer run sequentially.
- Existing caches remain:
  - `TRADER_LEADERBOARD_CACHE_TTL_SECONDS=60`
  - `FATBOT_VAULT_CACHE_TTL_SECONDS=60`
  - `HYPERLIQUID_ALL_MIDS_CACHE_TTL_SECONDS=15`


## v44 Copytrading vs FatBot Vaults sections
- Top navigation now changes the middle copy-management section:
  - `Copytrading` view shows only `Single Copytrading`.
  - `FatBot Vaults` view shows only multi-copy vault section.
- Copytrading middle section:
  - removed Multi Copytrading panel
  - Single Copytrading expanded to 10 slots
- FatBot Vaults middle section:
  - removed Single Copytrading panel
  - Multi Copytrading renamed to `FatBot Vaults`
  - expanded to 5 slots
- Slot limits are now:
  - Single Copytrading: 10
  - FatBot Vaults: 5


## v45 FatBot Vaults top-menu click fix
- Fixed top menu `FatBot Vaults` click handler.
- v44 defined `bindMainNavigation()` but did not call it after moving code around.
- Now the handler is registered before `loadAll()`, so clicking:
  - `Copytrading`
  - `FatBot Vaults`
  correctly switches the middle section.
- Also removed remaining hard-coded 5/3 slot checks in the create flow.


## v46 Wallet section logos
- Added Hyperliquid logo to Single Copytrading wallet rows and empty single slots.
- Added FatBot logo to FatBot Vault / multi-vault wallet rows and empty vault slots.
- Uses existing assets:
  - `frontend/assets/hyperliquid-logo.png`
  - `frontend/assets/fatbot-logo.png`
- Falls back to `HL` / `FB` initials if image assets are missing.


## v47 Empty slot logo alignment
- Empty Single Copytrading slots now align the Hyperliquid logo on the left, matching filled rows.
- Empty FatBot Vault slots now align the FatBot logo on the left, matching filled rows.
- The plus button remains on the right side.


## v48 Empty slot layout cleanup
- Fixed empty slot grid alignment for both Single Copytrading and FatBot Vaults.
- Slot index, logo, label, and plus button now align in one clean row like filled wallet rows.
- Empty slots have a subtle pink tinted background and dashed pink border.


## v49 Empty slot exact alignment
- Empty slots are forced to the same compact visual height as filled slots.
- Slot number, logo, text, and plus button are locked into one centered grid row.
- Pink background is stronger but still subtle.


## v50 Empty slot height match
- Empty slot height is now forced to 76px, matching filled wallet slot height.
- Existing horizontal alignment and pink background from v49 are preserved.


## v51 Empty slot green tint
- Changed empty slot background tint from pink to green.
- Empty slot height/alignment remains unchanged from v50.


## v52 Trader modal header spacing
- Adjusted Trader Profile modal header layout.
- COPY THIS TRADER button no longer overlaps with the close X button.
- Header uses a two-column grid with reserved right padding for the close button.


## v53 Leaderboard filters
Added a filter bar below the leaderboard tab bar for both Top Traders and FatBot Vaults.

Filters:
- Timeframe: 1D / 7D / 30D / 90D / All
- Sort by: PnL / Volume / Win Rate
- Min trades: 0 / 10 / 50 / 100
- Min active days: 0 / 3 / 7 / 14 / 30
- Limit: 50 / 100 / 200

Backend:
- `/api/traders` accepts query params:
  - `window`
  - `sortBy`
  - `limit`
  - `minTrades`
  - `minDaysActive`
- `/api/fatbot-vaults` accepts the same params.
- Top Traders params are passed to Hydromancer `userPnlLeaderboard`.
- FatBot Vaults use the timeframe for Hyperliquid fills/funding lookback and apply sort/min filters locally.


## v54 Profile filter + FatBot Vault data fix
- Fixed FatBot Vault data after v53:
  - `_summarize_fills()` now receives the active `window`, so fills do not fail internally.
- Trader Profile now uses the same active leaderboard filters as the list:
  - `window`
  - `sortBy`
  - `limit`
  - `minTrades`
  - `minDaysActive`
- `/api/traders/{address}` now accepts the same query params as `/api/traders`.
- PnL Window label now shows the active timeframe, e.g. `PnL Window (1D)`.
- Profile cache key now includes the active filter set, so 1D/7D/30D profiles do not mix.


## v55 Vault PnL from Hyperliquid portfolio endpoint
- FatBot Vault PnL now prefers the Hyperliquid `portfolio` endpoint for supported windows:
  - `1d` -> `day`
  - `7d` -> `week`
  - `30d` -> `month`
  - `all` -> `allTime`
- This is especially important for `all`, because `userFillsByTime` is capped and should not be treated as full all-time history.
- If portfolio stats are available, vault rows use:
  - `total_pnl` from portfolio PnL
  - `volume` from portfolio volume where available
  - `account_value` from accountValueHistory where available
- 90D currently still uses chunked fills because Hyperliquid portfolio has no native 90D bucket.


## v56 Current long/short and gross exposure metrics
Added live current exposure metrics from Hyperliquid `clearinghouseState` open positions.

Computed for FatBot Vaults and Top Trader profiles:
- Long notional = sum current notional of Long open positions
- Short notional = sum current notional of Short open positions
- Long / Short % = each side's share of total gross open exposure
- Gross exposure = (long notional + short notional) / account value
- Net exposure = (long notional - short notional) / account value

UI:
- Trader Profile now shows:
  - Long / Short
  - Gross Exposure
- Leaderboard row shows Gross when available, otherwise falls back to Win.


## v57 Top Traders current exposure enrichment
- Top Traders leaderboard rows now also get current long/short and gross exposure from Hyperliquid `clearinghouseState`.
- Hydromancer remains the strict source for Top Traders PnL/volume/win-rate/rank data.
- Exposure is not Hydromancer data; it is live Hyperliquid account state enrichment.
- New env controls:
  - `TOP_TRADERS_EXPOSURE_ENRICH=true`
  - `TOP_TRADERS_EXPOSURE_ENRICH_LIMIT=50`
  - `TOP_TRADERS_EXPOSURE_WORKERS=12`


## v58 Exposure empty-state clarification
- Some Hydromancer Top Traders have no current open Hyperliquid positions.
- For those wallets, Long/Short and Gross Exposure now display:
  - `0% / 0%`
  - `0.00x`
- Added a profile note:
  - `No current open positions`
- This avoids looking like the wallet/profile is broken when there are no live positions to calculate exposure from.


## v59 Account value fallback for zero-position wallets
- Fixed Top Trader profiles where `Account Value` showed `—` when the wallet had no open positions.
- Backend now tries:
  1. `clearinghouseState.marginSummary.accountValue`
  2. `portfolio.accountValueHistory` fallback
- This applies to Top Trader profiles, Top Trader exposure enrichment, and FatBot Vaults.
- A wallet can have `Live Positions = 0` and still show account value correctly.


## v60 Feed, ticker icons, and single copy naming
- Added token/ticker images to wallet open positions in Single Copytrading and FatBot Vault wallet detail rows.
- Live feed title now changes by top navigation:
  - Copytrading: `Live copytrading trades feed`
  - FatBot Vaults: `Live FatBot Vaults trades feed`
- Live feed row source logo changes by section:
  - Copytrading uses Hyperliquid logo
  - FatBot Vaults uses FatBot logo
- Feed row title is now a wallet/vault name rather than a generic ticker-only label.
- Added optional custom name field to Single Copytrading settings.
  - If the user skips it, the default name remains the copied wallet address.
