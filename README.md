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


## v61 My Vaults label
- Renamed leaderboard tab:
  - `My Copytrading` -> `My Vaults`
- Updated empty/hint copy to say copied wallets/vaults.


## v62 Market Type filter
Added `Market type` to the leaderboard filter bar:
- `All`: no market-type filter
- `Crypto`: requires >=70% of current open-position gross exposure in classic/non-TradFi Hyperliquid perp coins
- `TradFi`: requires >=70% of current open-position gross exposure in TradFi/XYZ-style coins

Backend:
- `/api/traders`, `/api/fatbot-vaults`, and `/api/traders/{address}` accept `marketType=all|crypto|tradfi`.
- Classification uses live Hyperliquid `clearinghouseState` positions after Top Traders are fetched from Hydromancer.
- Hydromancer remains the source for PnL/volume/win-rate/rank; market type is our live position classification.

Env:
- `MARKET_TYPE_EXPOSURE_THRESHOLD=70`
- `MARKET_TYPE_TRADFI_COINS=XYZ,SPX,SPY,NASDAQ,NDX,QQQ,DJI,DOW,TSLA,NVDA,AAPL,MSFT,GOOGL,META,AMZN,COIN,MSTR`


## v63 Market Type filter speed/fix
- Market Type filter no longer runs expensive live-position enrichment when `Market type = All`.
- For `Crypto` / `TradFi`, backend now scans more Hydromancer candidates first:
  - `MARKET_TYPE_SCAN_LIMIT=200`
- Then it enriches current positions and returns the selected UI limit.
- Wallets with no current open positions are excluded from Crypto/TradFi because there is no live exposure to classify.
- Faster defaults:
  - `TOP_TRADERS_EXPOSURE_ENRICH_LIMIT=200`
  - `TOP_TRADERS_EXPOSURE_WORKERS=24`
- Added clearer empty-state text explaining that market type uses current open positions.


## v64 Market Type threshold 70%
- Changed Market Type classification threshold from 90% to 70%.
- Applies to both:
  - Crypto: >=70% current gross exposure in classic/non-TradFi HL perp coins
  - TradFi: >=70% current gross exposure in TradFi/XYZ-style coins
- Env default is now:
  - `MARKET_TYPE_EXPOSURE_THRESHOLD=70`


## v65 Market Type position classification fix
- Fixed the Market Type filter bug:
  - v64 computed long/short/gross exposure but did not attach `market_type` to each row.
  - Because of that, `Crypto` and `TradFi` filters returned no rows.
- `_attach_current_exposure_metrics()` now also attaches:
  - `crypto_exposure_pct`
  - `tradfi_exposure_pct`
  - `market_type`
  - `market_type_reason`
- Future processing now uses `as_completed()` so completed Hyperliquid calls are consumed immediately.
- Default scan size reduced for speed:
  - `MARKET_TYPE_SCAN_LIMIT=100`
  - `TOP_TRADERS_EXPOSURE_ENRICH_LIMIT=100`
- You can still increase them in `.env` if you want broader scanning.


## v66 Market Type + Volume sort fix
- Fixed `Market type = Crypto` + `Sort by = Volume`.
- Problem: v65 scanned only one Hydromancer slice using the selected sort. For `volume`, many high-volume rows can have no current open positions, so the market filter returned zero.
- New logic for Crypto/TradFi filters:
  - fetch multiple Hydromancer slices:
    - selected sort
    - totalPnl
    - volume
    - winRate
  - dedupe by wallet
  - enrich current Hyperliquid positions
  - classify Crypto/TradFi
  - sort locally by the selected sort
- Defaults:
  - `MARKET_TYPE_SCAN_LIMIT=150`
  - `TOP_TRADERS_EXPOSURE_ENRICH_LIMIT=150`


## v67 Filter audit and balanced Market Type scan
Full filter-section audit against current endpoint behavior.

Validated endpoint usage:
- Hydromancer `userPnlLeaderboard`
  - Used only for Top Traders leaderboard PnL / volume / win-rate / rank.
  - Params used: `window`, `sortBy`, `limit`, `minTrades`, `minDaysActive`.
- Hyperliquid `clearinghouseState`
  - Used for live current positions, account value, long/short exposure, gross exposure, and market type classification.
- Hyperliquid `portfolio`
  - Used for FatBot Vault portfolio PnL/account value where supported.
- Hyperliquid `userFillsByTime`
  - Used as fallback/window fill stats, especially where portfolio bucket is unavailable.
- Hyperliquid `userFunding`
  - Used for funding display.

Market Type fix:
- Previous scanner appended all rows from the selected sort first. With `Sort by Volume`, the enrichment budget could be consumed by high-volume wallets with no current positions.
- New scanner fetches multiple Hydromancer slices and interleaves them rank-by-rank:
  - selected sort
  - totalPnl
  - volume
  - winRate
- Then it enriches current positions and classifies:
  - Crypto if >=70% current gross notional is non-TradFi perp coins
  - TradFi if >=70% current gross notional is TradFi/XYZ coins
- Added safer notional fallback:
  - positionValue
  - size * live/mark price
  - size * entry price

Env defaults:
- `MARKET_TYPE_EXPOSURE_THRESHOLD=70`
- `MARKET_TYPE_SCAN_LIMIT=150`
- `MARKET_TYPE_MAX_CANDIDATES=240`
- `TOP_TRADERS_EXPOSURE_ENRICH_LIMIT=240`
- `TOP_TRADERS_EXPOSURE_WORKERS=24`


## v68 Trader profile positions consistency fix
- Fixed profile modal showing `Live Positions > 0` while the positions list was empty.
- Root cause:
  - Profile fetch reset `t["positions"] = []` before refreshing Hyperliquid state.
  - If the fresh profile enrichment failed, but the leaderboard row already had exposure metrics/open-position count, the modal showed exposure but no position rows.
- Fixes:
  - Preserve existing enriched positions from the leaderboard row.
  - Only replace them with fresh positions if the fresh clearinghouseState parse succeeds.
  - `_extract_positions_from_state()` now skips malformed individual positions instead of failing the whole profile.
- Frontend empty message no longer falsely says exposure is zero if API state is inconsistent.


## v69 Top 500 + TradFi 40% threshold
- Added `Limit = 500` option in the leaderboard filter bar.
- Backend now allows `limit` up to 500.
- Market Type scan defaults increased:
  - `MARKET_TYPE_SCAN_LIMIT=500`
  - `MARKET_TYPE_MAX_CANDIDATES=500`
  - `TOP_TRADERS_EXPOSURE_ENRICH_LIMIT=500`
- TradFi classification threshold lowered:
  - `MARKET_TYPE_TRADFI_THRESHOLD=40`
- Crypto threshold remains stricter by default:
  - `MARKET_TYPE_CRYPTO_THRESHOLD=70`
- Backwards-compatible:
  - `MARKET_TYPE_EXPOSURE_THRESHOLD` can still override the crypto threshold if `MARKET_TYPE_CRYPTO_THRESHOLD` is not set.


## v70 Hyperliquid market registry for XYZ/TradFi tickers
Added a local market registry for classifying Hyperliquid perp tickers.

New files:
- `backend/app/market_registry.py`
- `backend/data/market_registry.json` is created after refresh

New Hyperliquid client methods:
- `meta()`
- `meta_and_asset_ctxs()`

New endpoints:
- `GET /api/market-registry`
  - returns registry summary and detected TradFi/XYZ symbols
- `POST /api/market-registry/refresh`
  - fetches Hyperliquid `metaAndAssetCtxs`, rebuilds local registry, and saves it

Market Type filter now classifies position coins with:
1. Hyperliquid market registry from `metaAndAssetCtxs`
2. raw ticker prefix rules, default `XYZ`
3. manual env overrides:
   - `MARKET_TYPE_TRADFI_COINS`
   - `MARKET_TYPE_TRADFI_PREFIXES`

Current defaults:
- `MARKET_TYPE_TRADFI_THRESHOLD=40`
- `MARKET_TYPE_CRYPTO_THRESHOLD=70`
- `MARKET_TYPE_TRADFI_PREFIXES=XYZ`
- `MARKET_REGISTRY_AUTO_REFRESH=true`
- `MARKET_REGISTRY_MAX_AGE_SECONDS=86400`
- `MARKET_REGISTRY_CACHE_TTL_SECONDS=3600`

This makes the TradFi filter independent from a purely hardcoded ticker list and allows us to detect new XYZ-style Hyperliquid markets when they appear in metadata.


## v71 Loading fix + safe market registry
Emergency fix for v70 page stuck in loading.

Root cause:
- v70 market registry could call Hyperliquid `metaAndAssetCtxs` during normal page load.
- That could block `/api/fatbot-vaults` or market classification, and because the frontend used `Promise.all`, one slow/failing endpoint kept the whole UI loading.

Fixes:
- `MARKET_REGISTRY_AUTO_REFRESH` default changed to `false`.
- Normal leaderboard/page loading uses cached/manual fallback registry only.
- To refresh real HL ticker registry, call manually:
  - `POST /api/market-registry/refresh`
- Frontend `loadAll()` now uses `Promise.allSettled()` so one failed endpoint does not block the whole app.
- Hyperliquid default timeout reduced:
  - `HYPERLIQUID_TIMEOUT=12`

Recommended env:
- `MARKET_REGISTRY_AUTO_REFRESH=false`
- `MARKET_REGISTRY_MAX_AGE_SECONDS=86400`
- `MARKET_REGISTRY_CACHE_TTL_SECONDS=3600`


## v72 Python 3.8 registry import fix
Emergency fix for local Windows Python 3.8.

Root cause:
- `backend/app/market_registry.py` used the Python 3.9+ annotation:
  - `tuple[List[Dict[str, Any]], List[Dict[str, Any]]]`
- Python 3.8 raises:
  - `TypeError: 'type' object is not subscriptable`

Fix:
- Replaced `tuple[...]` with `Tuple[...]`
- Added `Tuple` import from `typing`
- Cache-busted frontend to `app.js?v=72` / `styles.css?v=72`


## v73 TradFi debug scan + wider discovery
- TradFi candidate scan widened up to 2000 deduped Hydromancer candidates.
- Non-TradFi market scans default to 800 candidates.
- Added diagnostic endpoint:
  - `GET /api/debug/tradfi-scan?window=30d&sortBy=totalPnl&limit=500`

Use this endpoint to verify:
- whether Hydromancer returned candidates
- whether those candidates have live open HL positions
- which coins were found
- whether any coin was classified as TradFi/XYZ


## v74 TradFi presence filter
The debug scan proved TradFi positions exist, but the previous 40% threshold hid them.

Observed example:
- `coin_counts` contained `SPX` classified as `tradfi`
- `tradfi_count` was 0 because no wallet had >=40% TradFi exposure
- Some wallets had SPX/TradFi exposure around 0.2% or 0.56% while the rest was crypto

Fix:
- Market Type = TradFi now means: wallet has any current TradFi/XYZ/SPX position.
- Crypto remains threshold-based at the configured crypto threshold.
- Added:
  - `has_tradfi_position`
  - `has_crypto_position`
  - `market_filter_mode`
- UI label changed from `TradFi >40%` to `TradFi live`.

This matches the practical goal: discover wallets currently trading TradFi/XYZ markets even if TradFi is a small part of their total gross exposure.


## v75 TradFi = 40% of open-position count
Changed TradFi filter from exposure-notional logic to open-position-count logic.

Correct rule:
- If wallet has 10 open positions and 1 is TradFi, TradFi position share = 10%.
- It passes TradFi only if TradFi open-position count share is >= 40%.

New metrics:
- `tradfi_position_count`
- `crypto_position_count`
- `total_position_count`
- `tradfi_position_count_pct`
- `crypto_position_count_pct`

Env:
- `MARKET_TYPE_TRADFI_POSITION_COUNT_THRESHOLD=40`

Market Type behavior:
- TradFi: position-count percentage threshold
- Crypto: exposure-notional threshold remains `MARKET_TYPE_CRYPTO_THRESHOLD`


## v76 TradFi Any discovery option
Added a second TradFi filter mode because the debug data showed:
- SPX/TradFi positions exist,
- but no scanned wallet currently has >=40% of open positions in TradFi.

Market Type options:
- `TradFi >=40% positions`:
  - strict rule: `tradfi_position_count / total_position_count >= 40%`
- `TradFi any live position`:
  - discovery rule: wallet has at least 1 current TradFi/XYZ/SPX position

Debug endpoint now also returns:
- `tradfi_any_count`
- `tradfi_any_rows`

This lets us discover real live SPX/TradFi wallets first, then decide whether 40% is too strict for the current Hydromancer candidate universe.


## v77 XYZ/TradFi asset-class classification
Clarified and broadened TradFi classification.

For this dashboard, `XYZ/TradFi` means:
- XYZ / HIP-3 / builder-style markets
- stocks
- equity indices / ETFs
- commodities
- metals
- oil / energy markets

Default manual TradFi symbols now include:
- Indices / ETFs: `SPX, SPY, NASDAQ, NDX, QQQ, DJI, DOW, IWM, RUT`
- Stocks: `TSLA, NVDA, AAPL, MSFT, GOOGL, GOOG, META, AMZN, COIN, MSTR, NFLX, AMD, AVGO, PLTR`
- Commodities / metals / oil: `PAXG, XAU, GOLD, XAG, SILVER, WTI, BRENT, OIL, USOIL, UKOIL, CRUDE, NATGAS, NG, COPPER`

Registry classification now inspects the full Hyperliquid universe asset object, not only the short displayed ticker.
It also stores `asset_class`:
- `xyz`
- `stock`
- `index`
- `commodity`
- `tradfi_manual`
- `crypto`

UI labels changed to:
- `XYZ/TradFi >=40% positions`
- `XYZ/TradFi any position`


## v78 Real XYZ DEX ticker extraction + HIP-3 position scan
This fixes the actual issue: XYZ DEX markets must be discovered from Hyperliquid HIP-3 perp dex metadata, not guessed from short tickers.

Official HL info endpoints used:
- `perpDexs` to retrieve all perpetual dexes
- `meta` / `metaAndAssetCtxs` with `dex` to retrieve metadata for a specific HIP-3 perp dex
- `clearinghouseState` with `dex` to read user positions on that HIP-3 perp dex

New behavior:
- `MARKET_TYPE_TRADFI_DEXES=xyz` controls which HIP-3 dex names are considered XYZ/TradFi.
- `/api/market-registry/refresh` now:
  1. calls `perpDexs`
  2. finds the `xyz` dex
  3. calls `metaAndAssetCtxs(dex="xyz")`
  4. stores every ticker from that XYZ dex in the local registry
- Trader enrichment now checks:
  - main/default perp dex
  - every configured XYZ/TradFi dex, e.g. `xyz`
- Positions now include:
  - `dex`
  - `qualified_coin`, e.g. `xyz:TSLA`
- Market filters now classify positions as TradFi if they come from the configured XYZ dex, even when the short ticker alone is ambiguous.

Important:
- After installing this version, call:
  - `POST /api/market-registry/refresh`
- Then check:
  - `GET /api/market-registry`
- You should see `tradfi_dexes` and `tradfi_symbols` populated from XYZ DEX metadata.


## v79 XYZ DEX position scan fix
v78 added XYZ DEX registry, but the leaderboard enrichment still fetched only the main/default `clearinghouseState` in one code path.

v79 fixes that:
- Top Traders enrichment now fetches:
  - main/default clearinghouseState
  - configured XYZ/HIP-3 dex clearinghouseState, default `dex="xyz"`
- Trader profile fetch also uses the same multi-dex helper.
- `tradfi_any` now gets the same wider enrichment budget as strict `tradfi`.

This is the important part for live filtering: HIP-3/XYZ positions are not guaranteed to appear in default clearinghouseState; Hyperliquid supports a `dex` parameter for `clearinghouseState`, so we now explicitly query it.


## v80 XYZ logo cleanup
Changes:
- Removed visible `xyz:` / `XYZ:` prefixes from displayed ticker names.
- All XYZ / HIP-3 DEX instruments now use one fixed asset logo:
  - `frontend/assets/xyz-dex-logo.png`
  - served as `/static/assets/xyz-dex-logo.png`
- Added placeholder file:
  - `frontend/assets/PUT_XYZ_DEX_LOGO_HERE.txt`

What to upload:
- Put your chosen XYZ / HIP-3 DEX logo into:
  `frontend/assets/xyz-dex-logo.png`

Display result:
- Example:
  - before: `XYZ:xyz:NVDA`
  - after: `NVDA`
- All such instruments now share the same fixed XYZ logo.


## v81 Fast Trader Profile
Trader profile opening was slow because every modal open could trigger:
- allMids
- default clearinghouseState
- XYZ/HIP-3 dex clearinghouseState
- portfolio fallback

New fast behavior:
- If the leaderboard row already has enriched positions/exposure, profile returns immediately from cached leaderboard data.
- Normal Top Trader profiles use only main/default `clearinghouseState`.
- XYZ/HIP-3 dex profile scan is only used when opened from an XYZ/TradFi filter, or when explicitly enabled.
- `allMids` is disabled during profile open by default.
- portfolio fallback is disabled during profile open by default.
- profile cache TTL increased from 120s to 300s.

New env controls:
- `PROFILE_FAST_MODE=true`
- `PROFILE_FETCH_ALL_MIDS=false`
- `PROFILE_INCLUDE_XYZ_DEX=false`
- `PROFILE_PORTFOLIO_FALLBACK=false`
- `PROFILE_CACHE_TTL_SECONDS=300`

If you want full slow profile refresh for debugging, set:
- `PROFILE_FAST_MODE=false`
- `PROFILE_FETCH_ALL_MIDS=true`
- `PROFILE_INCLUDE_XYZ_DEX=true`
- `PROFILE_PORTFOLIO_FALLBACK=true`


## v82 Parallel loading / speed focus
Speed-focused update without intentionally reducing data/functionality.

Backend:
- Hydromancer market filter candidate slices now fetch in parallel:
  - selected sort
  - totalPnl
  - volume
  - winRate
- Hyperliquid profile/XYZ DEX state calls now fetch main + XYZ dex states in parallel.
- Hyperliquid HTTP calls use a shared requests Session with connection pooling.
- Moderate default worker increase:
  - `TOP_TRADERS_EXPOSURE_WORKERS=36`
- Profile cache TTL increased:
  - `PROFILE_CACHE_TTL_SECONDS=600`

Frontend:
- Initial dashboard loading now renders each section as soon as its endpoint returns.
- Filter changes update Top Traders and FatBot Vaults independently as soon as each request returns.
- One slower endpoint no longer visually blocks the whole page.

New/updated env defaults:
- `HYPERLIQUID_TIMEOUT=8`
- `HYPERLIQUID_CONNECT_TIMEOUT=3`
- `HYPERLIQUID_READ_TIMEOUT=8`
- `HTTP_POOL_CONNECTIONS=80`
- `HTTP_POOL_MAXSIZE=160`
- `HYDROMANCER_SCAN_WORKERS=4`
- `PROFILE_DEX_WORKERS=6`
- `TOP_TRADERS_EXPOSURE_WORKERS=36`
- `PROFILE_CACHE_TTL_SECONDS=600`

Functionality preserved:
- Same Hydromancer filters and candidate slices.
- Same main + configured XYZ DEX position checks.
- Same market classification rules.
- Changes are primarily concurrency, caching, HTTP pooling, and progressive rendering.


## v83 Account Value column + dynamic My tab label
Small UI update.

Changes:
- Main leaderboard row metric changed:
  - from `Volume`
  - to `Account Value`
- Top Traders account value is fetched from Hyperliquid `clearinghouseState`
  for a capped number of visible rows.
- Ranking/filter logic is not changed.
- Dynamic last leaderboard tab label:
  - Copytrading page: `My Copytrading`
  - FatBot Vaults page: `My Vaults`

New env controls:
- `TOP_TRADERS_ACCOUNT_VALUE_ENRICH=true`
- `TOP_TRADERS_ACCOUNT_VALUE_ENRICH_LIMIT=50`
- `TOP_TRADERS_ACCOUNT_VALUE_WORKERS=24`


## v84 TradFi profile + table consistency fix
Fixes based on TradFi filter testing.

Changes:
- Main table final metric column is always `Win`.
  - It no longer switches to `Gross` when exposure is available.
- Account Value is also filled for market-type filtered rows after filtering,
  capped to visible rows.
- Trader profile no longer returns 404 just because the clicked wallet is missing
  from a re-run filtered slice.
  - Added direct live fallback profile:
    - merges Hydromancer row if found
    - fetches Hyperliquid live state directly
    - includes XYZ dex state when opened from TradFi filters

Functionality preserved:
- Ranking/filter rules unchanged.
- TradFi / XYZ detection unchanged.
- This fixes display consistency and profile lookup robustness.


## v85 Real profile cache fix, not hiding missing positions
This version is specifically meant to expose/fix the actual mismatch instead of showing fake zero-position profiles.

Problem:
- TradFi/XYZ rows can be produced by widened live scans and already contain positions.
- Opening profile re-ran lookup logic and sometimes missed that wallet, then fallback could show 0 positions.

Fix:
- `get_trader()` now first searches existing in-memory leaderboard caches for the exact clicked address.
- If found, it returns the exact row and positions that were visible in the UI.
- Direct fallback no longer silently acts like a solved empty profile; it adds:
  - `positions_status=direct_live_lookup_returned_no_positions`
  - `profile_warning`
- Frontend also falls back to the exact visible row if profile API fails, with a warning.

New debug endpoint:
- `GET /api/debug/profile-lookup/{address}`


## v86 Restore normal trader profiles
Fixes the v85 regression.

Root cause:
- v85 searched the leaderboard cache before doing live profile enrichment.
- Normal Top Traders rows in `Market Type = All` intentionally do not contain `positions`.
- v85 returned those rows as profiles anyway, so normal trader profiles looked like they had 0 live positions.

Fix:
- Cache row profile shortcut is now used only when the cached row already contains live positions.
- For normal Top Traders rows without `positions`, the backend continues to the normal live profile path and fetches Hyperliquid state.
- Debug endpoint now distinguishes:
  - `contains_address`
  - `matching_rows_with_positions`
  - `found_in_leaderboard_cache_with_positions`

Endpoint:
- `GET /api/debug/profile-lookup/{address}`


## v87 Audited HL/Hydromancer position fix
Full position-fetch review against current docs.

Important corrections:
- Hydromancer `clearinghouseState` now supports explicit `dex`.
- When available, backend uses:
  - `type=clearinghouseState`
  - `dex=ALL_DEXES`
  to retrieve native + all HIP-3 DEX positions in one call.
- Added robust parser for common ALL_DEXES response shapes:
  - native state object
  - dict of dex -> state
  - wrappers: `data`, `result`, `states`, `dexStates`, `clearinghouseStates`
  - list and `[dex, state]` pair shapes
- Hyperliquid public endpoint remains fallback:
  - default/native `clearinghouseState`
  - configured XYZ/HIP-3 dex `clearinghouseState` calls in parallel.
- Fast profile no longer returns cached rows simply because `hl_state_status=ok`.
  It only uses cached row shortcut when that row actually contains positions.
- Empty direct fallback is marked as diagnostic, not as a confirmed zero-position result.

New env:
- `USE_HYDROMANCER_ALL_DEX_STATE=true`
- `HYDROMANCER_ALL_DEX_VALUE=ALL_DEXES`

Sources reviewed:
- Hyperliquid info/perpetual endpoints: `clearinghouseState`, `meta`, `metaAndAssetCtxs`, `perpDexs`
- Hydromancer `clearinghouseState` docs showing `dex=ALL_DEXES`.


## v88 Profile/Table metadata merge fix
Fixes mismatch where leaderboard row showed Account Value but trader profile preview was blank.

Root cause:
- The table can have `account_value` from lightweight leaderboard enrichment.
- Profile live fetch can fail to retrieve positions/account value for that wallet.
- The profile result did not merge the already-visible table metadata.

Fix:
- Backend now has two separate cache helpers:
  - `_find_trader_row_in_leaderboard_caches` for metadata merge
  - `_find_trader_in_leaderboard_caches` only when cached row already has positions
- Profile results merge non-position fields from the visible cached leaderboard row:
  - account_value
  - rank
  - pnl
  - volume
  - win_rate
  - trades
  - account age
  - funding
- Frontend also merges the clicked preview row into the profile response if fields are missing.
- Live positions are still not faked. Position data is only shown when actually present.


## v91 Hot wallets panel
Right-top panel renamed from Multi Copytrading Leaderboard to `Hot wallets`.

Behavior:
- Same panel exists in both main views:
  - Copytrading
  - FatBot Vaults
- Copytrading view:
  - shows a placeholder mix of normal leaderboard wallets and FatBot index/vault rows
  - metric label: `Copied by users`
  - sorted by placeholder copied-user count
- FatBot Vaults view:
  - shows FatBot vault/pool style rows
  - metric label: `Active in FatBot Vaults`
  - sorted by placeholder active-vault count
- Rows use the same visual style/data style as leaderboard rows:
  - logo
  - title/address
  - metric
  - PnL
  - Account Value
  - Win
  - Copy action
- Max rendered rows are capped to 12 so the panel scrolls inside the existing module area.


## v92 Hot wallets readability
Small UI change:
- Removed the `Win` column from the right-side `Hot wallets` panel only.
- Main leaderboard is unchanged.
- Hot wallets rows now have more horizontal space for title, metric, PnL, Account Value and button.


## v93 Hot wallets layout fix
Fixes the right-side Hot wallets panel layout.

Changes:
- Removed `Account Value` column from Hot wallets only.
- Hot wallets now uses its own grid layout instead of borrowing the wide main leaderboard row grid.
- Full available panel width is used.
- Title/subtitle are ellipsized cleanly instead of overlapping.
- Remaining columns:
  - logo
  - wallet/vault title
  - Copied by users / Active in FatBot Vaults
  - PnL
  - Copy button


## v95 Reliable PnL display
Reverted Hydromancer Top Traders PnL back to USD.

Reason:
- Calculating trader PnL % as `totalPnl / current account_value` is not reliable.
- If a trader withdraws funds, current account value can be small and the PnL %
  becomes meaningless or massively inflated.
- This version does not invent a percent return for external traders.

Display rule:
- Hydromancer Top Traders / normal wallets: selected-window PnL in USD from Hydromancer.
- FatBot Vaults: keep existing percentage PnL.
- If we later get a reliable return/ROI field or point-in-time equity baseline from
  Hydromancer, we can add a proper percentage again.


## v96 Unified PnL in USD
Changed display so both external wallets and FatBot Vaults show PnL in USD.

Reason:
- Trader PnL % is not reliable when current account value is distorted by deposits/withdrawals.
- To keep the UI consistent, FatBot Vaults are also shown in USD.

Display rule:
- Hydromancer Top Traders / external wallets: selected-window `totalPnl` in USD.
- FatBot Vaults: real USD PnL field where available.
- Percentage PnL is not shown in the main wallet/vault rows.


## v97 Default 80% visual zoom
Makes the app at normal browser zoom (`100%`) visually look like the previous local Chrome `80%` zoom.

Implementation:
- Adds CSS-level app zoom:
  - `--fatbot-ui-zoom: 0.8`
  - `--fatbot-ui-zoom-inverse: 1.25`
- Expands body width/height before zoom so the scaled UI still fills the viewport.
- Applies only on screens wider than 1000px.
- Mobile/narrow screens stay at normal scale.

Changed:
- `frontend/styles.css`
- `frontend/index.html`
