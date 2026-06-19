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
