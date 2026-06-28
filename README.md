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


## v108 Two-column UI + real 7D PnL sparkline
Baseline: v97.

Major UI changes:
- Removed the active right-side Hot wallets / Live feed column.
- Current middle Copytrading modules now become the right column.
- PnL Leaderboard is widened to roughly 2/3 of the screen.
- Added mini PnL sparkline column to Top Traders rows.

Sparkline data:
- Source: Hyperliquid `portfolio` endpoint, bucket:
  - `day` for 1D leaderboard window
  - `week` for all other windows
- Uses `pnlHistory` directly in USD.
- No fake chart:
  - if `pnlHistory` is missing or has fewer than 2 points, the row shows `—`.
- Enrichment is capped for performance:
  - `TOP_TRADERS_SPARKLINE_ENRICH_LIMIT=14`
  - `TOP_TRADERS_SPARKLINE_WORKERS=8`

Changed:
- `backend/app/services.py`
- `frontend/app.js`
- `frontend/styles.css`
- `frontend/index.html`


## v109 Profile portfolio charts
Adds large profile charts while keeping the leaderboard mini chart conservative.

Leaderboard mini chart:
- Still uses Hyperliquid `portfolio.pnlHistory`.
- Displayed as USD PnL trend.
- No fake points; missing history shows `—`.

Trader profile modal:
- Adds large charts from Hyperliquid `portfolio`:
  - PnL USD
  - Account value
  - PnL / equity %
- `PnL / equity % = pnl_usd / account_value * 100` per chart point.
- This is explicitly not cashflow-adjusted ROI.
- If a series has fewer than 2 real points, it is not shown.

Backend:
- Adds `portfolio_chart_points` to trader profile responses.
- Uses:
  - `day` bucket when leaderboard window is 1D
  - `week` bucket otherwise
- Env:
  - `PROFILE_PORTFOLIO_CHARTS=true`
  - `PROFILE_CHART_MAX_POINTS=80`


## v110 Async openTrader fix
Fixes frontend JavaScript syntax error from v109:

- Error: `Uncaught SyntaxError: await is only valid in async functions`
- Cause: `openTrader(address)` used `await` but was declared as a normal function.
- Fix: changed it to `async function openTrader(address)`.

Changed:
- `frontend/app.js`
- `frontend/index.html` cache bump


## v111 Single top profile chart
Wallet/trader profile modal update:
- Portfolio chart section moved to the very top of the modal.
- Replaced three separate chart cards with one large active chart.
- Added toggle buttons:
  - PnL USD
  - Account Value
  - PnL / Equity %
- Chart switches instantly on the frontend using already loaded `portfolio_chart_points`.

No backend data model change from v109/v110.


## v112 Async final fix
Fixes the recurring frontend syntax error:

- `Uncaught SyntaxError: await is only valid in async functions`
- Ensures every `openTrader(address)` declaration is `async function openTrader(address)`.

Also cache-bumped:
- `styles.css?v=112`
- `app.js?v=112`

JS syntax check:
```text
exit=0
STDOUT=
STDERR=
```


## v113 Wallet click fix
Fixes wallet/trader click not opening after v111/v112.

Cause:
- Loading-state modal template called `profileChartsHtml(trader)` before `trader` existed.
- This caused a frontend ReferenceError immediately after clicking a wallet.

Fix:
- Removed the chart call from the loading skeleton.
- Kept the chart at the top of the final profile after API data loads.

JS syntax check:
```text
exit=0
STDOUT=
STDERR=
```


## v114 Profile layout cleanup
Profile modal update:
- Trader profile header with logo and Copy button is first at the top.
- Portfolio chart is below the profile header.
- Chart toggle buttons moved to the bottom-right of the chart card.
- Removed Account Age and Total Funding cards to save one detail row.

Changed:
- `frontend/app.js`
- `frontend/styles.css`
- `frontend/index.html`


## v115 Profile 3x3 stats
Profile detail stats update:
- Account Age is restored.
- Total Funding remains removed.
- Live profile stats are now 9 cards in a 3 × 3 grid.
- Chart/header layout unchanged from v114.

Changed:
- `frontend/app.js`
- `frontend/styles.css`
- `frontend/index.html`


## v116 Leaderboard columns and height
Leaderboard update:
- Removed the Rank column completely.
- Added Volume column.
- Added Gross Exp. column.
- Extended the left PnL Leaderboard module downward so more wallets fit and it aligns better with the copytrading module on the right.

Changed:
- `frontend/app.js`
- `frontend/styles.css`
- `frontend/index.html`


## v117 Leaderboard fix
Fixes based on v116:
- Leaderboard height reduced by about two wallet rows.
- Gross Exp. column is now populated from live Hyperliquid current exposure enrichment, not just displayed as an empty UI column.
- Mini PnL sparkline enrichment default limit increased from 14 to 50, so rows lower in the scroll can still show real charts.

Notes:
- Gross exposure is only shown when live current positions/account value can be fetched.
- Missing Gross Exp. still displays `—` instead of fake data.
- Missing sparkline still displays `—` instead of fake data.

Changed:
- `backend/app/services.py`
- `frontend/styles.css`
- `frontend/index.html`


## v118 Profile chart restore
Fixes profile charts disappearing after v117.

Cause:
- v117 started enriching all-market leaderboard rows with live positions/exposure.
- `get_trader()` then found the clicked wallet in the leaderboard cache and returned that cached row early.
- That early return happened before `_attach_portfolio_chart_data()`, so the modal had no `portfolio_chart_points`.

Fix:
- Cached leaderboard profile path now also calls `_attach_portfolio_chart_data()` before returning.

Changed:
- `backend/app/services.py`
- `frontend/index.html` cache bump
- `frontend/app.js` cache marker only


## v119 Leaderboard column order
Trader row columns reordered to:
- PnL
- Value
- Volume
- Exposure
- Win Rate
- 7D PnL graph

Changed:
- `frontend/app.js`
- `frontend/styles.css`
- `frontend/index.html`


## v120 Leaderboard categories
Replaces old leaderboard tabs with requested categories:
- Top TradFi
- Top Crypto
- Top Bull
- Top Bears
- Top FatBot Selection
- Favourite

Logic:
- Top TradFi: backend marketType=`tradfi`, sorted by PnL.
- Top Crypto: backend marketType=`crypto`, sorted by PnL.
- Top Bull: long exposure share > 80%, sorted by PnL.
- Top Bears: short exposure share > 80%, sorted by PnL.
- Top FatBot Selection: manual list in `FATBOT_SELECTION_ADDRESSES`, sorted by PnL.
- Favourite: locally starred wallets/vaults.

Manual selection list:
- Edit `frontend/app.js`
- Add addresses to:
  `const FATBOT_SELECTION_ADDRESSES = [];`

Changed:
- `frontend/index.html`
- `frontend/app.js`
- `frontend/styles.css`


## v121 Category runtime fix
Fixes v120 not loading leaderboard.

Cause:
- HTML tabs were updated to new category names.
- Runtime JS helper functions for category loading were missing from the packaged `app.js`.
- `bindLeaderboardCategoryTabs()` was called but not defined, so JS stopped before `loadAll()` and no `/api/traders` request was sent.

Fix:
- Added missing category helpers:
  - `FATBOT_SELECTION_ADDRESSES`
  - `categoryMarketType`
  - `syncCategoryToMarketFilter`
  - `reloadLeaderboardOnly`
  - `bindLeaderboardCategoryTabs`
- Initial category defaults to Top TradFi.
- Categories now trigger proper backend reloads.

Changed:
- `frontend/app.js`
- `frontend/index.html`
- `frontend/styles.css`


## v122 Fixed categories, no filter bar
Removed the free filter bar under leaderboard categories.

Remaining fixed categories:
- Top TradFi
- Top Crypto
- Top Bull
- Top Bears
- Top FatBot Selection
- Favourite

Fixed query assumptions:
- window: 30D
- sort: PnL
- minTrades: 0
- minDaysActive: 0
- limit: 50
- marketType is controlled by category:
  - Top TradFi -> tradfi
  - Top Crypto -> crypto
  - others -> all, then local category filtering

Changed:
- `frontend/index.html`
- `frontend/app.js`
- `frontend/styles.css`


## v123 Category click/load fix
Fixes v122 stuck on "Loading traders..." and category buttons not working.

Cause:
- v122 called category runtime functions, but the packaged app.js did not include them.
- `syncCategoryToMarketFilter()` was undefined before initial `loadAll()`, so JS stopped before API requests.

Fix:
- Restored category runtime:
  - `categoryMarketType`
  - `syncCategoryToMarketFilter`
  - `reloadLeaderboardOnly`
  - `bindLeaderboardCategoryTabs`
  - `FATBOT_SELECTION_ADDRESSES`
- Ensured `loadAll()` is async.
- Kept filter bar removed.


## v124 Speed + profile chart fallback
Goal:
- Keep mini leaderboard charts.
- Keep large profile charts.
- Reduce leaderboard loading time.

Speed changes:
- Reduced default live exposure enrichment caps:
  - TradFi/current-position scan default: 250 rows
  - Non-TradFi exposure scan default: 120 rows
  - Market-type candidate scan default: 300 TradFi / 180 non-TradFi
- These are still configurable with env variables:
  - `TOP_TRADERS_EXPOSURE_ENRICH_LIMIT`
  - existing market/candidate env settings where applicable

Chart protection:
- Large profile chart now falls back to the already-loaded real mini sparkline points if `portfolio_chart_points` is missing.
- This prevents the profile graph from disappearing when the slower full portfolio chart attach is unavailable.
- No fake values are invented; fallback uses real `pnl_sparkline` values from Hyperliquid portfolio PnL history.

Changed:
- `backend/app/services.py`
- `frontend/app.js`
- `frontend/index.html`


## v125 Top Trades + TradFi 70%
Changes:
- Added new fixed category: `Top Trades`.
  - No TradFi/Crypto/Bull/Bear filter.
  - Fixed 30D PnL ranking.
- Top TradFi threshold changed to 70% open-position count share.
- Top Crypto remains 70% crypto exposure threshold.
- Mini leaderboard charts remain.
- Large profile charts remain.

Categories:
- Top Trades
- Top TradFi
- Top Crypto
- Top Bull
- Top Bears
- Top FatBot Selection
- Favourite

Changed:
- `backend/app/services.py`
- `frontend/index.html`
- `frontend/app.js`
- `frontend/styles.css`


## v126 Server-side leaderboard snapshot cache
Major performance update:
- Added server-side precomputed leaderboard snapshots in SQLite.
- Users no longer trigger slow TradFi/Crypto/Bull/Bear scans on every category click.
- Background worker refreshes snapshots every 5 minutes by default.
- UI reads `/api/leaderboard-snapshot/{category}` for instant category display.
- Last good snapshot remains available even if a refresh fails.

No external database required:
- Uses existing local `copytrading.db` SQLite.
- New tables:
  - `leaderboard_snapshots`
  - `leaderboard_snapshot_rows`

New endpoints:
- `GET /api/leaderboard-snapshot/{category}`
- `GET /api/leaderboard-snapshot-status`
- `POST /api/leaderboard-snapshot-refresh`

Config:
- `LEADERBOARD_SNAPSHOT_ENABLED=true`
- `LEADERBOARD_SNAPSHOT_REFRESH_SECONDS=300`
- `LEADERBOARD_SNAPSHOT_POOL_LIMIT=200`
- `LEADERBOARD_SNAPSHOT_VISIBLE_LIMIT=50`

Preserved:
- Mini leaderboard sparkline.
- Large profile charts.
- Profile chart fallback from mini sparkline.
- All copytrading/favourite/manual selection functionality.


## v127 FatBot Selection manual addresses
Added 39 manual wallet addresses to FatBot Selection.

FatBot Selection behavior:
- Built server-side in the background snapshot worker.
- Uses the manual address list.
- Wallets with no current open positions are hidden.
- Sorted by 30D PnL.
- Mini leaderboard chart remains.
- Profile charts remain.

Config:
- `FATBOT_SELECTION_WORKERS=12`

Changed:
- `frontend/app.js`
- `backend/app/services.py`
- `frontend/index.html`


## v128 Snapshot chart fix
Fixes:
- Mini 7D PnL charts missing in some categories.
- FatBot Selection rows showing without mini charts.
- Old v126/v127 SQLite snapshots can remain stale, so v128 adds a snapshot version marker.

What changed:
- Every final snapshot category is sparkline-enriched after filtering.
- Old snapshot rows without v128 version are treated as stale and background refresh is triggered.
- FatBot Selection source label is now `FatBot Selection wallet`.
- Large profile charts remain protected.

Important:
- After installing v128, restart backend and let it rebuild snapshots once.
- Or call `POST /api/leaderboard-snapshot-refresh`.


## v129 FatBot Selection real wallet scan
Fixes the FatBot Selection category.

What was wrong before:
- FatBot Selection used the wrong enrichment path.
- Some rows showed zero PnL/volume because live stats overwrote/failed instead of preserving Hydromancer stats.
- It only checked limited/default state in some cases, so some wallets with positions could be missed.

v129 behavior:
- Every manual wallet is scanned directly.
- Current positions are fetched across all relevant dexes.
- Wallets with no open positions are hidden.
- Hydromancer PnL/volume/win stats are preserved when available.
- Hyperliquid portfolio/fills are used only as fallback.
- Mini charts and large profile charts remain.


## v130 FatBot Selection public HL fix
Fixes:
- FatBot Selection no longer uses a broken/partial enrichment path.
- FatBot Selection is now built directly from public Hyperliquid endpoints:
  - current positions across relevant dexes
  - account value
  - exposure
  - portfolio PnL/account value history
  - fills fallback for volume/trades/win rate
- Wallets with no open positions are hidden.
- Profile modal can now open FatBot Selection rows from SQLite snapshot rows.
- Snapshot version bumped to force rebuild.

Mini chart fix:
- Every final snapshot category now gets a second chart-enrichment pass.
- If the mini sparkline is missing, it falls back to profile portfolio chart data.


## v132 FatBot Selection audit
Adds a diagnostic endpoint instead of another blind patch.

New endpoint:
- `GET /api/debug/fatbot-selection-audit`

It returns every manual FatBot Selection wallet with:
- included/excluded decision
- reason
- open_positions
- positions_by_dex
- dex_state_status
- account_value
- portfolio chart availability
- mini sparkline availability
- errors

Use this to identify exactly why a wallet with real open positions is being missed by the backend scan.


## v133 Wallet aliases, Hypurrscan links, 30D labels, profile modal close
Changes:
- Leaderboard rows now have a pencil icon to rename any wallet locally in the browser.
- Leaderboard rows now have a Hypurrscan redirect icon using dynamic address URLs:
  `https://hypurrscan.io/address/<address>#more`
- Leaderboard metric labels for PnL / Volume / Win Rate are fixed as 30D.
- The leaderboard API query is forced to `window=30d` and `sortBy=totalPnl`.
- FatBot Selection shows the "Longterm profitable" label above the leaderboard title when that tab is active.
- Trader profile modal no longer shows the top-right X.
- Trader profile modal now has a top-left back arrow.
- Clicking outside the trader profile modal closes it.


## v134 Redirect icon + Longterm profitable fix
Fixes:
- Redirect icon is now an external-link SVG icon, matching the requested visual style.
- `Longterm profitable` display for active FatBot Selection is now controlled with inline `style.display`, not only the `.hidden` class, so it reliably appears above the PnL Leaderboard title when FatBot Selection is active.


## v135 Profile wallet actions
Adds the same wallet actions to the trader profile modal:
- pencil icon to rename the wallet nickname locally;
- external-link icon to open the wallet on Hypurrscan;
- dynamic Hypurrscan URL based on the opened wallet address.


## v136 FatBot tab badge + 30D charts
Changes:
- `Longterm profitable` is now displayed inside the active `Top FatBot Selection` tab, on the right side.
- Removed the old label above the `PnL Leaderboard` title.
- Leaderboard/profile chart logic now uses the 30D/month portfolio bucket when the leaderboard is on 30D.
- Labels changed from 7D wallet history / 7D PnL to 30D wallet history / 30D PnL.
- Snapshot version bumped to rebuild cached chart rows.


## v137 Copy Wallet modal redesign
Changes direct `Copy Wallet` modal:
- Top section shows the selected wallet 30D PnL chart.
- Shows selected wallet address/name only; removed selecting another leaderboard wallet and custom wallet override.
- Wallet name input moved near the selected wallet address.
- Shows Account Value, 30D PnL, and Gross Exposure metrics.
- Keeps exposure multiplier and max drawdown controls.
- Shows Cross margin as fixed/non-editable.
- CTA changed to `Create and fund copytrading wallet`.


## v138 Copy modal tweaks
Changes:
- Direct Copy Wallet modal now starts with the 30D PnL chart; removed the visible top `Create Copytrading Wallet / Copying...` header for this flow.
- Hypurrscan external-link icon moved next to `COPY SOURCE`.
- `Name wallet` changed to `Copytrading name`.
- Placeholder changed to `Name your copytrading strategy`.
- Other copy settings remain unchanged.


## v139 Multiplier wording + top tab readability
Changes:
- `Copy multiplier` renamed to `Gross exposure multiplier`.
- Leaderboard top category menu has reduced inner padding/gaps and slightly larger tab font.
- FatBot Selection badge spacing tightened so the tab text has more room.


## v140 Copy modal close behavior
Changes:
- Copy Wallet modal no longer uses the top-right X close button.
- Copy Wallet modal now has a top-left back arrow.
- Clicking outside the Copy Wallet modal closes it.


## v141 FatBot Selection 6M graphs
Changes:
- FatBot Selection keeps main leaderboard metrics at 30D:
  - 30D PnL
  - 30D Volume
  - 30D Win Rate
  - live Gross Exposure
- FatBot Selection chart history is now 6M.
- 6M chart data is built from public Hyperliquid `portfolio` allTime history and trimmed locally to the last 180 days.
- Wallets without live open positions are explicitly hidden from FatBot Selection even if manually supplied.
- Old snapshot rows are invalidated via snapshot version bump.

Hyperliquid public endpoints used:
- `clearinghouseState` for live positions/account value/exposure.
- `portfolio` for pnlHistory/accountValueHistory.
- `userFillsByTime` fallback remains for 30D volume/trades/win-rate where available.


## v142 Stable FatBot Selection refresh
Fixes refresh flicker in the custom manual FatBot Selection section.

Problem:
- Public Hyperliquid endpoints can intermittently return empty/missing position or portfolio-history data.
- Previous versions replaced the whole snapshot on every refresh, so the visible wallet count and mini charts could change every 2 minutes.

v142 behavior:
- Main FatBot Selection metrics remain 30D.
- FatBot Selection chart remains 6M.
- Wallets with no live open positions are still hidden by default.
- But one bad scan no longer deletes a previously-good wallet/chart.
- Last-good FatBot rows are retained for `FATBOT_SELECTION_LAST_GOOD_TTL_SECONDS`, default 1800 seconds / 30 minutes.
- If a current scan loses a chart but the previous snapshot had it, the chart is preserved.
- If a current scan returns empty while a previous snapshot exists, the previous snapshot is protected.

Optional env:
- `FATBOT_SELECTION_LAST_GOOD_TTL_SECONDS=1800`
- Set to `0` to disable last-good retention.


## v143 Hyperliquid 429 protection for FatBot Selection
Fixes the audit/snapshot issue where every manual wallet could be excluded because Hyperliquid returned `429` for both `main` and `xyz`.

Changes:
- Hyperliquid public client now has a global request throttle.
- Hyperliquid public client retries 429/5xx with backoff.
- FatBot Selection default scan workers reduced from 10 to 2.
- Per-wallet dex scan default workers reduced from 6 to 1.
- `allMids` is fetched once per FatBot Selection build instead of once per wallet.
- FatBot Selection still keeps 30D metrics and 6M charts.
- Wallets without live positions remain hidden, but 429 no longer immediately turns every wallet into "no positions" as easily.

Optional env tuning:
- `HYPERLIQUID_MIN_REQUEST_INTERVAL_SECONDS=0.10`
- `HYPERLIQUID_MAX_RETRIES=4`
- `HYPERLIQUID_RETRY_BACKOFF_SECONDS=0.75`
- `FATBOT_SELECTION_WORKERS=2`
- `PROFILE_DEX_WORKERS=1`


## v144 FatBot Vault builder
Work is focused on the FatBot Vaults category/view.

Changes:
- Leaderboard row CTA becomes `Add to vault` when the app is in FatBot Vaults view.
- Clicking `Add to vault` adds the wallet to the first free trader slot in the open vault builder.
- If the vault builder is not open, it opens the first free unlocked FatBot Vault slot and inserts the trader.
- Right-side FatBot Vault area now shows 10 slots.
- First 3 vault slots are unlocked.
- Slots 4–10 are blurred/locked:
  - slot 4 requires 100,000 USD Perps volume
  - slot 5 requires 200,000 USD Perps volume
  - each next slot adds 100,000 USD
- Clicking an unlocked empty vault slot opens the FatBot Vault builder.
- Builder step 1:
  - manual wallet slots
  - min 3 traders
  - max 10 traders
  - `add trader slot` button adds another trader input
- Builder step 2:
  - drawdown
  - Vault exposure multiplier
  - Cross fixed info
- Final CTA: `Create and fund vault address`.


## v145 Inline FatBot Vault builder
Adjusts the v144 vault builder to match the requested UX:
- Empty FatBot Vault slots no longer open a modal.
- Clicking an unlocked free vault slot expands an inline setup panel directly under that slot.
- Wallet adding uses dropdowns populated from the left leaderboard plus manual 0x input.
- `Add to vault` from the left leaderboard inserts into the first free inline trader slot.
- Locked slots now show visible lock text and blur/backdrop styling:
  `Reach X USD Perps volume to unlock this slot.`


## v146 Vault input-only trader slots
Changes:
- Removed the dropdown selector from FatBot Vault trader slots.
- Each trader slot is now a single empty input.
- Placeholder: `Pick wallet from leaderboard or paste your own`.
- `Add to vault` from the left leaderboard still fills the first free input slot.


## v147 Add to vault CTA fix
Fix:
- Leaderboard CTA now robustly shows `Add to vault` whenever the FatBot Vaults right panel is active/visible.
- Click behavior also uses the same robust vault-add mode and inserts the wallet into the first free vault input.


## v148 Locked vault slots
Fix:
- Locked FatBot Vault slots now show visible text.
- Text format uses `Reach 100 000 USD Perps volume to unlock this slot.`
- Each following locked slot increases by 100 000 USD.
- Blur/backdrop overlay is stronger while the unlock text stays readable.


## v149 Locked slot single-line text
Fix:
- Locked FatBot Vault slot unlock text is now one horizontal line across the slot.
- Removed the extra `Locked Vault Slot` label from the visible message.
- Keeps slot number + lock icon on the left.


## v150 Locked slot visible text
Fix:
- Locked vault slot text is no longer inside a narrow `small` element.
- Text is displayed directly in the flex row and spans the available slot width.
- Keeps slot number and lock icon on the left.


## v151 Default live FatBot Vault
Adds a default live vault in the FatBot Vaults section.

Default vault address:
- `0x0baFb25EF191bFe7A2727E14F5BbfC36610EC62A`

Behavior:
- The default vault is injected as the first FatBot Vault slot in the right panel.
- Its row uses live data from the existing FatBot Vault / Hyperliquid profile pipeline.
- Clicking this vault opens a modal based on the single-wallet profile modal:
  - VAULT STATS tab: portfolio chart, metrics, and live positions.
  - WALLET MANAGEMENT tab: quick leaderboard-like rows for saved member wallets.
- Wallet Management:
  - remove wallet with trash icon and confirmation dialog;
  - add wallet by 0x address;
  - Save settings stores member wallet settings in browser localStorage.


## v152 Default vault modal speed + placeholders
Fix:
- Default vault popup no longer stays on `Loading live vault data...`.
- It renders immediately from the already-loaded FatBot Vault leaderboard row.
- It refreshes the full live profile in the background with a timeout, so slow/429 public API calls do not block the UI.
- Wallet Management now preloads 7 placeholder wallets from the current leaderboard when no saved members exist.
- Placeholder wallet members are saved in localStorage and can be removed/edited through Wallet Management.


## v153 Wallet Management chart previews
Change:
- Wallet Management rows now include a `30D Chart` mini PnL sparkline preview, same source as the leaderboard row.
- Placeholder members pulled from the leaderboard show their existing 30D chart when available.


## v154 Default vault live data + charts fix
Fix:
- The default vault modal no longer tries to load the vault through `/api/traders/{address}`.
- It now refreshes from `/api/fatbot-vaults`, which is the correct source for platform FatBot Vault rows.
- Backend `list_fatbot_vaults` now attaches real Hyperliquid portfolio chart data to vault rows.
- VAULT STATS renders immediately from cached row data, then updates from `/api/fatbot-vaults`.
- If chart data is not yet ready, the modal shows a chart-loading placeholder instead of staying stuck.
- Wallet Management can also receive `Add to vault` directly while the management tab is open.


## v155 Default vault modal render fix
Fix:
- Removed undefined frontend helper calls inside the default vault modal (`tradesDisplay`, `accountAgeDisplay`) that could leave the modal stuck on the loading card.
- `renderDefaultVaultModalContent()` is now wrapped in a safe fallback so a widget error cannot leave an infinite spinner.
- VAULT STATS uses the same existing dashboard display helpers as the normal wallet/profile detail:
  - `profileChartsHtml`
  - `pnlUsdValue`
  - `moneyOrDash`
  - `grossExposureDisplay`
  - live positions list rendering
- If portfolio chart points are missing but the leaderboard row has a sparkline, the modal creates a chart fallback from that sparkline.


## v156 Vault Stats 3x3 metrics grid
Change:
- VAULT STATS metric cards are now displayed as 9 cards in 3 rows x 3 columns, matching the single wallet profile layout.
- Includes:
  - PnL Window (30D)
  - Account Value
  - Long / Short
  - Gross Exposure
  - 30D Win Rate
  - 30D Trades
  - Account Age
  - 30D Volume
  - Live Positions


## v157 Vault Stats forced 3-column grid
Fix:
- VAULT STATS cards no longer inherit the older `.detail-grid` two-column rules.
- Cards use a dedicated `.vault-stats-grid-3x3` grid.
- Forced layout: 3 columns x 3 rows on desktop.


## v158 Default vault modal unified size
- Wallet Management tab now keeps the same large modal footprint as Vault Stats.
- Added a dedicated `default-vault-modal-card` class on the trader modal while the default vault modal is open.
- Added a desktop `min-height` to `#defaultVaultModalBody` so the two tabs keep a unified visual flow.


## v159 Vault cards: unified modal + 7D mini chart
- All filled FatBot Vault rows on the right now open the same unified vault modal flow instead of using inline dropdown expansion.
- Replaced the `Drift` column on FatBot Vault rows with a mini PnL sparkline chart (7D-first fallback).
- Wallet Management now works generically for any opened FatBot Vault modal and stores custom member edits locally per vault.


## v160 FatBot Vaults top-right How it Works section
- On the FatBot Vaults main view, the top-right PnL Allocation card is replaced with a looping How it Works section.
- It rotates 5 steps in a 3-second loop.
- Regular Copytrading view still shows the original PnL Allocation card.


## v161 vault status / price / close flow polish
- FatBot Vault cards now use a **pulsing green dot** instead of a wide ACTIVE pill, so the row fits better.
- In Vault Stats, **Live Price** values are formatted with cleaner decimal precision.
- In Vault Modal → **Wallet Management**, there is now a red **Close Vault** button.
- Clicking **Close Vault** opens the required browser input prompt for the withdraw wallet, then a confirmation step.


## v162 FatBot Vault compact row / close / Liq formatting
- FatBot Vault leaderboard rows were compacted so the green status dot stays **in the same single row**.
- Closing a vault now **removes it from My Vaults** and leaves an **empty slot** in the portfolio area.
- Vault modal position rows now format **Liq** with the same decimal precision cleanup as Live Price.


## v163 FatBot Vault single-row layout fix
- Restored the richer FatBot Vault row appearance closer to the previous version.
- Fixed the vault card row so **all elements stay in one single row** by using the correct 8-column grid:
  slot index, logo, label, value, total pnl, exposure, 7D chart, status dot.
- Kept v162 behavior improvements: close vault clears the slot, and Liq uses cleaned decimal formatting.


## v164 Remove extra preset vaults + styled Close Vault dialog
- `FatBot Vault #2` and `FatBot Vault #3` are hidden from the FatBot Vaults portfolio.
- Closing a vault now uses a styled in-app dialog instead of browser prompt/confirm as the first step.
- Close Vault flow:
  1. Click `Close Vault`.
  2. Enter withdraw wallet address.
  3. Click `Close Vault`.
  4. Confirm the final close action.
- Confirmed close still removes the vault from My Vaults and leaves an empty slot.


## v165 Create vault after hidden presets
Fix:
- Hidden preset vaults `FatBot Vault #2` and `FatBot Vault #3` no longer count against the first 3 unlocked vault slots.
- `Start FatBot Vault` / `Create and fund vault address` now checks only visible usable vaults.
- Create flow now shows a real error if `/api/pools` does not return `wallet_id`, instead of silently doing nothing.


## v166 Delete preset vaults + fix Create Vault
Fix:
- `FatBot Vault #2` and `FatBot Vault #3` are no longer only hidden in the UI.
- The frontend removes them from state and calls DELETE for them if they still exist.
- The backend `list_wallets()` also purges those two old preset/demo vault wallets and their pool rows from SQLite.
- Create Vault now supports the requested `min 3 / max 10` trader wallets end-to-end:
  - frontend validation already had min 3 / max 10;
  - backend schema changed from max 5 to max 10;
  - backend service changed from min 2 / max 5 to min 3 / max 10.
- Added a confirmation alert after successful vault creation.


## v167 Create Vault preview fix
Critical fix:
- Removed label-based deletion/filtering of `FatBot Vault #2` / `FatBot Vault #3`.
- Those labels are valid for newly created vaults, so v166 could create a vault and immediately filter/delete it from the preview.
- After successful `/api/pools` + activation, the created wallet is now inserted directly into frontend state and rendered immediately before the backend refresh.
- Result: newly created vault appears in the FatBot Vaults preview right away.


## v168 Close Vault dialog confirmation fix
Fix:
- Removed browser `window.confirm()` from Close Vault because it could appear blocked/hidden and make the button look dead.
- Close Vault now uses an in-app two-click flow:
  1. Enter withdraw wallet.
  2. Click `Close Vault`.
  3. Dialog changes to final confirmation state.
  4. Click `Confirm Close Vault`.
- Closed vault is removed immediately from frontend state and the slot becomes empty.


## v169 Single Copytrading modal flow
Change:
- Single Copytrading wallet rows no longer open inline/dropdown details.
- Clicking any existing single copy wallet opens a modal dialog.
- Modal includes:
  - wallet value / available / realized PnL / unrealized PnL / gross exposure / drift;
  - open positions;
  - `Close Copytrading` action.
- `Close Copytrading` uses the same in-app two-step withdraw confirmation flow as Close Vault:
  1. enter withdraw wallet;
  2. click `Close Copytrading`;
  3. confirm with `Confirm Close Copytrading`.
- On final confirm, wallet is deleted and immediately removed from the My Copytrading preview, leaving an empty slot.


## v170 Model Single Copy slot
Change:
- Added one model Single Copytrading slot in the Copytrading view.
- Source wallet:
  - `0x0baFb25EF191bFe7A2727E14F5BbfC36610EC62A`
- The model slot uses available live/cached data from the existing FatBot Vault / trader data pipeline.
- It appears as `Model Single Copy` and has a `MODEL` badge.
- Clicking it opens the same Single Copytrading modal from v169, with visible metrics and positions.
- Closing the model single slot hides it locally and leaves an empty slot, without calling backend delete.


## v171 Model Single live data fix
Fix:
- The model Single Copy slot is now always visible, even if older localStorage had hidden it.
- It no longer shows fake fallback values.
- It uses the exact FatBot Vault live row for:
  - `0x0baFb25EF191bFe7A2727E14F5BbfC36610EC62A`
- When `/api/fatbot-vaults` finishes loading, the single preview rerenders with live values/positions.
- Opening the model single modal also refreshes `/api/fatbot-vaults` in the background and updates the modal.


## v172 Token icon resolver
Change:
- Unknown coin icons now use a backend resolver instead of only local frontend mappings.
- New endpoints:
  - `GET /api/token-icon/{coin}` redirects to the best icon URL.
  - `GET /api/token-icons?coins=BTC,ETH,SOL` returns resolver metadata for multiple coins.
- Resolver priority:
  1. local/manual overrides for Hyperliquid + common tickers;
  2. CoinGecko search by symbol;
  3. k-prefix fallback, e.g. `kPEPE -> PEPE`;
  4. CryptoCompare coin list fallback;
  5. frontend ticker badge fallback if no icon is found.
- Results are cached in backend memory for 7 days to avoid heavy API calls.
