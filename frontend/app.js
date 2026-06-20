const API = '';
let state = {
  traders: [],
  wallets: [],
  livePositions: [],
  pools: [],
  fatbotVaults: [],
  selectedTrader: null,
  selectedMultiTraders: [],
  selectedVaultToCopy: null,
  liveFeedTransactions: [],
  liveFeedTimer: null,
  expandedWallets: new Set(),
  closingWallets: new Set(),
  isCreatingCopy: false,
  vaultName: '',
  singleWalletName: '',
  copySetupMode: 'single',
  mainView: 'copytrading',
  selectedSlot: null,
  activeLeaderTab: 'top',
  leaderboardFilters: {
    window: '30d',
    sortBy: 'totalPnl',
    minTrades: 0,
    minDaysActive: 0,
    limit: 50,
  },
  favourites: new Set(JSON.parse(localStorage.getItem('fatbot_copy_favourites') || '[]')),
  wizardStep: 0,
  generatedWallet: null,
  wizardSettings: {
    multiplier: 1,
    max_leverage: 3,
    max_position_pct: 30,
    max_gross_exposure_pct: 150,
    stop_drawdown_pct: -20,
    min_trade_size_usd: 10,
    slippage_tolerance_pct: 0.3,
  },
};

const fmtUsd = (v) => Number(v || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 });
const fmtPct = (v) => `${Number(v || 0) > 0 ? '+' : ''}${Number(v || 0).toFixed(1)}%`;
const shortAddress = (s) => (s && s.length > 12 ? `${s.slice(0, 8)}...${s.slice(-4)}` : (s || ''));
const positiveClass = (v) => (Number(v || 0) >= 0 ? 'positive' : 'negative');
function sideClass(side) {
  return String(side || '').toLowerCase().includes('short') ? 'short-side' : 'long-side';
}

function isHydro(t) {
  return t && t.source === 'hydromancer';
}
function pnlDisplay(t) {
  if (t && t.source === 'fatbot_vault') return fmtPct(t.pnl_pct ?? t.pnl_30d ?? 0);
  return isHydro(t) ? fmtUsd(t.total_pnl || 0) : fmtPct(t.pnl_30d || 0);
}
function pnlNumber(t) {
  if (t && t.source === 'fatbot_vault') return Number(t.pnl_pct ?? t.pnl_30d ?? 0);
  return isHydro(t) ? Number(t.total_pnl || 0) : Number(t.pnl_30d || 0);
}
function rankDisplay(t, fallbackIndex = 0) {
  return `#${Number(t.rank || fallbackIndex + 1)}`;
}
function winRateDisplay(t) {
  return `${Number(t.win_rate || 0).toFixed(1)}%`;
}
function exposureShareDisplay(t) {
  const longPct = Number(t?.long_exposure_share_pct ?? t?.long_exposure_pct ?? 0);
  const shortPct = Number(t?.short_exposure_share_pct ?? t?.short_exposure_pct ?? 0);
  if (!longPct && !shortPct) return '—';
  return `${longPct.toFixed(0)}% / ${shortPct.toFixed(0)}%`;
}
function grossExposureDisplay(t) {
  const gross = Number(t?.gross_exposure || 0);
  if (!gross) return '—';
  return `${gross.toFixed(2)}x`;
}
function hydroPairsDisplay(t, max = 8) {
  const pairs = Array.isArray(t.traded_pairs) ? t.traded_pairs : [];
  if (!pairs.length) return '—';
  const shown = pairs.slice(0, max).join(', ');
  return pairs.length > max ? `${shown} +${pairs.length - max}` : shown;
}
function moneyOrDash(v) {
  const n = Number(v || 0);
  return n ? fmtUsd(n) : '—';
}


const $ = (id) => document.getElementById(id);
function safeClassRemove(id, className) {
  const el = $(id);
  if (el) el.classList.remove(className);
  return el;
}

function traderBadgeClass(i) {
  return ['alt-a', 'alt-b', 'alt-c', 'alt-d', 'alt-e', 'alt-f'][i % 6];
}
function traderBadgeLabel(address) {
  return (address || 'TR').replace('0x', '').slice(0, 2).toUpperCase();
}
function leaderLogoHtml(item, index = 0, extraClass = '') {
  const cls = extraClass ? ` ${extraClass}` : '';
  if (item && item.source === 'fatbot_vault') {
    return `<div class="leader-logo fatbot-logo${cls}"><img src="/static/assets/fatbot-logo.png" alt="FatBot" onerror="this.remove(); this.parentElement.textContent='FB';"></div>`;
  }
  if (item && item.source === 'hydromancer') {
    return `<div class="leader-logo hl-logo${cls}"><img src="/static/assets/hyperliquid-logo.png" alt="Hyperliquid" onerror="this.remove(); this.parentElement.textContent='HL';"></div>`;
  }
  return `<div class="avatar-badge ${traderBadgeClass(index)}${cls}">${traderBadgeLabel(item && item.address)}</div>`;
}


function walletBadgeLabel(mode) {
  return mode === 'pool' ? 'MC' : 'SC';
}
function coinClass(coin) {
  return (coin || '').toLowerCase();
}
function tokenIconUrl(coin) {
  const c = String(coin || '').toUpperCase().split(':').pop();
  const icons = {
    BTC: 'https://assets.coingecko.com/coins/images/1/large/bitcoin.png',
    ETH: 'https://assets.coingecko.com/coins/images/279/large/ethereum.png',
    SOL: 'https://assets.coingecko.com/coins/images/4128/large/solana.png',
    HYPE: 'https://assets.coingecko.com/coins/images/50882/large/hyperliquid.jpg',
    DOGE: 'https://assets.coingecko.com/coins/images/5/large/dogecoin.png',
    ARB: 'https://assets.coingecko.com/coins/images/16547/large/arb.jpg',
    OP: 'https://assets.coingecko.com/coins/images/25244/large/Optimism.png',
    LINK: 'https://assets.coingecko.com/coins/images/877/large/chainlink-new-logo.png',
    AVAX: 'https://assets.coingecko.com/coins/images/12559/large/Avalanche_Circle_RedWhite_Trans.png',
    BNB: 'https://assets.coingecko.com/coins/images/825/large/bnb-icon2_2x.png',
    XRP: 'https://assets.coingecko.com/coins/images/44/large/xrp-symbol-white-128.png',
    SUI: 'https://assets.coingecko.com/coins/images/26375/large/sui-ocean-square.png',
    WLD: 'https://assets.coingecko.com/coins/images/31069/large/worldcoin.jpeg',
    FARTCOIN: 'https://assets.coingecko.com/coins/images/50891/large/fart.jpg',
    ZEC: 'https://assets.coingecko.com/coins/images/486/large/circle-zcash-color.png',
    TAO: 'https://assets.coingecko.com/coins/images/28452/large/ARUsPeNQ_400x400.jpeg',
  };
  return icons[c] || '';
}

function coinIconHtml(coin, iconUrl = '') {
  const safeCoin = (coin || '?').toString();
  const src = iconUrl || tokenIconUrl(safeCoin);
  if (src) {
    return `<img class="coin-img" src="${src}" alt="${safeCoin}" loading="lazy" onerror="this.replaceWith(Object.assign(document.createElement('div'), {className: 'coin-icon ' + coinClass('${safeCoin}'), textContent: '${safeCoin[0] || '?'}'}))">`;
  }
  return `<div class="coin-icon ${coinClass(safeCoin)}">${safeCoin[0] || '?'}</div>`;
}
function saveFavourites() {
  localStorage.setItem('fatbot_copy_favourites', JSON.stringify([...state.favourites]));
}

async function api(path, opts = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!res.ok) {
    let body = await res.text();
    try {
      const parsed = JSON.parse(body);
      body = parsed.detail || body;
    } catch (_) {}
    throw new Error(body);
  }
  return res.json();
}

function ensureUiState() {
  if (!state.expandedWallets) state.expandedWallets = new Set();
  if (!state.closingWallets) state.closingWallets = new Set();
  if (!state.selectedMultiTraders) state.selectedMultiTraders = [];
  if (!state.liveFeedTransactions) state.liveFeedTransactions = [];
}


function singleSlotLimit() {
  return 10;
}

function multiSlotLimit() {
  return state.mainView === 'fatbot-vaults' ? 5 : 5;
}

function isCopytradingView() {
  return state.mainView !== 'fatbot-vaults';
}

function isFatBotVaultsView() {
  return state.mainView === 'fatbot-vaults';
}


function leaderboardQueryString() {
  const f = state.leaderboardFilters || {};
  const params = new URLSearchParams({
    window: f.window || '30d',
    sortBy: f.sortBy || 'totalPnl',
    minTrades: String(f.minTrades ?? 0),
    minDaysActive: String(f.minDaysActive ?? 0),
    limit: String(f.limit ?? 50),
  });
  return params.toString();
}

function readLeaderboardFiltersFromDom() {
  state.leaderboardFilters = {
    window: document.getElementById('filterWindow')?.value || '30d',
    sortBy: document.getElementById('filterSortBy')?.value || 'totalPnl',
    minTrades: Number(document.getElementById('filterMinTrades')?.value || 0),
    minDaysActive: Number(document.getElementById('filterMinDays')?.value || 0),
    limit: Number(document.getElementById('filterLimit')?.value || 50),
  };
}

function bindLeaderboardFilters() {
  ['filterWindow', 'filterSortBy', 'filterMinTrades', 'filterMinDays', 'filterLimit'].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('change', async () => {
      readLeaderboardFiltersFromDom();

      const list = document.getElementById('traderList');
      if (list) {
        list.classList.add('loading');
        list.innerHTML = 'Loading leaderboard...';
      }

      try {
        const q = leaderboardQueryString();
        const [traders, fatbotVaults] = await Promise.all([
          api(`/api/traders?${q}`),
          api(`/api/fatbot-vaults?${q}`),
        ]);
        state.traders = traders;
        state.fatbotVaults = fatbotVaults;
        renderLeaderboardTabs();
        renderTraders();
      } catch (err) {
        console.error(err);
        const list = document.getElementById('traderList');
        if (list) list.innerHTML = `<div class="empty-state">Filter load failed: ${err.message || err}</div>`;
      }
    });
  });
}

async function loadAll() {
  ensureUiState();
  const [summary, traders, wallets, livePositions, pools, fatbotVaults] = await Promise.all([
    api('/api/summary'),
    api(`/api/traders?${leaderboardQueryString()}`),
    api('/api/wallets'),
    api('/api/live-positions'),
    api('/api/pools'),
    api(`/api/fatbot-vaults?${leaderboardQueryString()}`),
  ]);
  state.traders = traders;
  state.wallets = wallets;
  state.livePositions = livePositions;
  state.pools = pools;
  state.fatbotVaults = fatbotVaults;

  renderSummary(summary);
  renderLeaderboardTabs();
  renderTraders();
  renderCopySections(wallets);
  renderMultiLeaderboard(pools, wallets);
  renderLiveTraderFeed(livePositions);
}

function renderSummary(summary) {
  const metricValue = $('metricValue');
  const metricPnl = $('metricPnl');
  const metricWallets = $('metricWallets');
  const metricDrift = $('metricDrift');
  if (metricValue) metricValue.textContent = fmtUsd(summary.total_value);
  if (metricPnl) {
    metricPnl.textContent = summary.total_pnl >= 0 ? `+${fmtUsd(summary.total_pnl).replace('$', '$')}` : fmtUsd(summary.total_pnl);
    metricPnl.className = positiveClass(summary.total_pnl);
  }
  if (metricWallets) metricWallets.textContent = summary.active_wallets;
  if (metricDrift) metricDrift.textContent = `${Number(summary.avg_drift || 0).toFixed(1)}%`;

  const singleValue = state.wallets.filter(w => w.mode !== 'pool').reduce((a, w) => a + Number(w.value || 0), 0);
  const multiValue = state.wallets.filter(w => w.mode === 'pool').reduce((a, w) => a + Number(w.value || 0), 0);
  const available = state.wallets.reduce((a, w) => a + Number(w.available || 0), 0);
  const total = singleValue + multiValue + available;
  const pct = total > 0 ? Math.round((singleValue / total) * 100) : 48;

  if ($('allocSingle')) $('allocSingle').textContent = fmtUsd(singleValue);
  if ($('allocPool')) $('allocPool').textContent = fmtUsd(multiValue);
  if ($('allocAvailable')) $('allocAvailable').textContent = fmtUsd(available);
  if ($('allocPct')) $('allocPct').textContent = `${pct}%`;
}

function copiedTraderAddresses() {
  return new Set(
    state.wallets
      .filter(w => ['active', 'generated', 'paper'].includes(String(w.status || '').toLowerCase()))
      .map(w => String(w.copied_trader_address || '').toLowerCase())
      .filter(Boolean)
  );
}

function filteredTraders() {
  if (state.activeLeaderTab === 'fatbot') {
    return state.fatbotVaults || [];
  }

  if (state.activeLeaderTab === 'favourite') {
    const all = [...(state.traders || []), ...(state.fatbotVaults || [])];
    return all.filter(t => state.favourites.has(t.vault_id || t.address));
  }

  if (state.activeLeaderTab === 'my') {
    const copied = copiedTraderAddresses();
    const topCopied = (state.traders || []).filter(t => copied.has(String(t.address || '').toLowerCase()));
    const vaultCopied = (state.fatbotVaults || []).filter(v => copied.has(String(v.address || '').toLowerCase()) || copied.has(String(v.vault_id || '').toLowerCase()));
    return [...topCopied, ...vaultCopied];
  }

  return state.traders;
}


function renderLeaderboardTabs() {
  document.querySelectorAll('[data-leader-tab]').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.leaderTab === state.activeLeaderTab);
  });

  const hint = $('leaderboardHint');
  if (!hint) return;

  const f = state.leaderboardFilters || {};
  const sortLabel = f.sortBy === 'volume' ? 'Volume' : (f.sortBy === 'winRate' ? 'Win Rate' : 'PnL');
  const filterText = `${String(f.window || '30d').toUpperCase()} · sort ${sortLabel} · min trades ${f.minTrades ?? 0} · min active days ${f.minDaysActive ?? 0} · limit ${f.limit ?? 50}`;

  if (state.activeLeaderTab === 'top') {
    hint.textContent = `Top traders ranked by external PnL leaderboard data. ${filterText}`;
  } else if (state.activeLeaderTab === 'fatbot') {
    hint.textContent = `FatBot platform vaults and multi-copy indexes. ${filterText}`;
  } else if (state.activeLeaderTab === 'favourite') {
    hint.textContent = 'Favourite traders and vaults saved locally in this browser.';
  } else {
    hint.textContent = 'Your active copied traders and copied FatBot vaults.';
  }
}


function renderTraders() {
  const traders = filteredTraders();
  const el = safeClassRemove('traderList', 'loading');
  if (!el) return;

  if (!traders.length) {
    const msg = state.activeLeaderTab === 'favourite'
      ? 'No favourites yet. Click the star on a trader or vault.'
      : state.activeLeaderTab === 'my'
        ? 'No copied traders or vaults yet.'
        : state.activeLeaderTab === 'fatbot'
          ? 'No FatBot vaults available.'
          : 'No traders available.';
    el.innerHTML = `<div class="empty-state">${msg}</div>`;
    return;
  }

  el.innerHTML = traders.map((t, i) => {
    const favKey = t.vault_id || t.address;
    const isFav = state.favourites.has(favKey);
    const isVault = t.source === 'fatbot_vault';
    const isLive = isHydro(t) || isVault;
    const subtitle = isVault ? 'FatBot multi-copy vault' : (isLive ? 'Hydromancer PnL leaderboard' : t.label);
    const actionLabel = isVault ? 'Copy Vault' : 'Copy Wallet';

    return `
      <div class="trader-row hydro-trader-row ${isVault ? 'fatbot-vault-row' : ''}" data-address="${t.address}" data-vault-id="${t.vault_id || ''}">
        <button class="fav-btn ${isFav ? 'active' : ''}" data-fav="${favKey}" title="Favourite">${isFav ? '★' : '☆'}</button>
        ${leaderLogoHtml(t, i)}
        <div>
          <div class="row-title">${isVault ? (t.label || shortAddress(t.address)) : shortAddress(t.address)}</div>
          <div class="row-sub">${subtitle}</div>
        </div>
        <div>
          <div class="row-sub">Rank</div>
          <div class="rank">${rankDisplay(t, i)}</div>
        </div>
        <div>
          <div class="row-sub">PnL</div>
          <strong class="${positiveClass(pnlNumber(t))}">${pnlDisplay(t)}</strong>
        </div>
        <div class="optional-leader-col">
          <div class="row-sub">Volume</div>
          <strong>${isLive ? fmtUsd(t.volume || t.volume_traded || 0) : '—'}</strong>
        </div>
        <div class="optional-leader-col">
          <div class="row-sub">${grossExposureDisplay(t) !== '—' ? 'Gross' : 'Win'}</div>
          <strong>${grossExposureDisplay(t) !== '—' ? grossExposureDisplay(t) : (isLive ? winRateDisplay(t) : '—')}</strong>
        </div>
        <button class="copy-btn" data-copy="${t.address}" data-vault-copy="${isVault ? '1' : ''}">${actionLabel}</button>
      </div>
    `;
  }).join('');

  el.querySelectorAll('.trader-row').forEach(row => {
    row.addEventListener('click', (e) => {
      if (e.target.dataset.copy || e.target.dataset.fav) return;
      openTrader(row.dataset.address);
    });
  });
  el.querySelectorAll('[data-copy]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      openCopyWizard(btn.dataset.copy);
    });
  });
  el.querySelectorAll('[data-fav]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const key = btn.dataset.fav;
      if (state.favourites.has(key)) state.favourites.delete(key);
      else state.favourites.add(key);
      saveFavourites();
      renderTraders();
    });
  });
}



function copyWalletLogoHtml(mode) {
  const isPool = mode === 'pool';
  const src = isPool ? '/static/assets/fatbot-logo.png' : '/static/assets/hyperliquid-logo.png';
  const fallback = isPool ? 'FB' : 'HL';
  const cls = isPool ? 'fatbot-wallet-logo' : 'hl-wallet-logo';
  return `
    <div class="copy-wallet-logo ${cls}">
      <img src="${src}" alt="${fallback}" onerror="this.style.display='none';this.parentElement.classList.add('logo-fallback');this.parentElement.dataset.fallback='${fallback}'" />
    </div>
  `;
}

function renderCopySections(wallets) {
  const single = wallets.filter(w => w.mode !== 'pool');
  const multi = wallets.filter(w => w.mode === 'pool');

  const singlePanel = $('singleSectionPanel');
  const multiPanel = $('multiSectionPanel');

  if (isCopytradingView()) {
    if (singlePanel) singlePanel.style.display = '';
    if (multiPanel) multiPanel.style.display = 'none';

    if ($('singleSectionTitle')) $('singleSectionTitle').textContent = 'Single Copytrading';
    if ($('singleSectionText')) $('singleSectionText').textContent = 'Copy one selected trader per wallet. Maximum 10 single copy wallets.';
    if ($('singleLimit')) $('singleLimit').textContent = `${Math.min(single.length, singleSlotLimit())} / ${singleSlotLimit()}`;

    renderWalletSection('singleCopyList', single, 'single', singleSlotLimit());
    return;
  }

  if (singlePanel) singlePanel.style.display = 'none';
  if (multiPanel) multiPanel.style.display = '';

  if ($('multiSectionTitle')) $('multiSectionTitle').textContent = 'FatBot Vaults';
  if ($('multiSectionText')) $('multiSectionText').textContent = 'Create or manage FatBot vault copy indexes. Maximum 5 vaults.';
  if ($('multiLimit')) $('multiLimit').textContent = `${Math.min(multi.length, multiSlotLimit())} / ${multiSlotLimit()}`;

  renderWalletSection('multiCopyList', multi, 'multi', multiSlotLimit());
}

function renderWalletSection(elementId, wallets, type, slotLimit = null) {
  ensureUiState();
  const el = safeClassRemove(elementId, 'loading');
  if (!el) return;

  const maxSlots = slotLimit || (type === 'single' ? singleSlotLimit() : multiSlotLimit());
  const rows = [];

  for (let i = 0; i < maxSlots; i += 1) {
    const w = wallets[i];

    if (w) {
      const isExpanded = state.expandedWallets.has(String(w.id));
      const isClosing = state.closingWallets.has(String(w.id));
      rows.push(`
        <div class="wallet-slot-wrap">
          <div class="wallet-row compact-wallet fixed-slot filled-slot" data-wallet-id="${w.id}">
            <div class="slot-index">${i + 1}</div>
            ${copyWalletLogoHtml(w.mode)}
            <div>
              <div class="row-title">${w.label}</div>
              <div class="row-sub">${w.mode === 'pool' ? 'Multi copy wallet' : `Copying: ${String(w.copied_trader_address || '').startsWith('vault:') ? 'Multi Vault' : shortAddress(w.copied_trader_address || 'Not selected')}`}</div>
              <div class="progress"><i style="width:${Math.min(100, 35 + Number(w.gross_exposure || 0) * 25)}%"></i></div>
            </div>
            <div><div class="row-sub">Value</div><strong>${fmtUsd(w.value)}</strong></div>
            <div><div class="row-sub">Total PnL</div><strong class="${positiveClass(w.total_pnl)}">${fmtUsd(w.total_pnl)}</strong></div>
            <div><div class="row-sub">Exposure</div><strong>${Number(w.gross_exposure || 0).toFixed(2)}x</strong></div>
            <div><div class="row-sub">Drift</div><strong>${Number(w.drift || 0).toFixed(1)}%</strong></div>
            <div class="status-badge ${w.status}">${String(w.status || '').toUpperCase()}</div>
          </div>
          ${isExpanded ? walletExpandedPanel(w, isClosing) : ''}
        </div>
      `);
    } else {
      const label = type === 'single' ? 'Start Single Copytrading' : 'Start FatBot Vault';
      rows.push(`
        <button class="start-copy-card slot-card" data-start-copy="${type}" data-slot="${i + 1}">
          <span class="slot-index">${i + 1}</span>
          ${copyWalletLogoHtml(type === 'multi' ? 'pool' : 'single')}
          <span class="plus-mark">+</span>
          <strong>${label}</strong>
        </button>
      `);
    }
  }

  el.innerHTML = rows.join('');

  el.querySelectorAll('[data-start-copy]').forEach(startBtn => {
    startBtn.addEventListener('click', () => {
      const selectedType = startBtn.dataset.startCopy;
      if (selectedType === 'single') {
        openSlotSettings('single', Number(startBtn.dataset.slot || 1));
      } else {
        state.selectedMultiTraders = [];
        state.vaultName = '';
        openSlotSettings('multi', Number(startBtn.dataset.slot || 1));
      }
    });
  });

  el.querySelectorAll('[data-wallet-id]').forEach(row => {
    row.addEventListener('click', (e) => {
      if (e.target.closest('button') || e.target.closest('input')) return;
      const id = String(row.dataset.walletId);
      if (state.expandedWallets.has(id)) state.expandedWallets.delete(id);
      else state.expandedWallets.add(id);
      renderCopySections(state.wallets || []);
    });
  });

  el.querySelectorAll('[data-close-copy]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const id = String(btn.dataset.closeCopy);
      await api(`/api/wallets/${id}/close`, { method: 'POST' });
      state.closingWallets.add(id);
      await loadAll();
      state.expandedWallets.add(id);
      state.closingWallets.add(id);
      renderCopySections(state.wallets || []);
    });
  });

  el.querySelectorAll('[data-withdraw-delete]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const id = String(btn.dataset.withdrawDelete);
      const input = document.getElementById(`withdrawDest_${id}`);
      const dest = input ? input.value.trim() : '';
      if (!isValidWallet(dest)) {
        alert('Enter a valid destination wallet starting with 0x.');
        return;
      }
      const ok = confirm(`Confirm withdraw to ${dest} and delete this copytrading wallet?`);
      if (!ok) return;
      await api(`/api/wallets/${id}`, { method: 'DELETE' });
      state.expandedWallets.delete(id);
      state.closingWallets.delete(id);
      await loadAll();
    });
  });
}

function walletExpandedPanel(w, isClosing) {
  const positions = w.positions || [];
  const positionsHtml = positions.length ? positions.map(p => `
    <div class="wallet-position-row">
      ${coinIconHtml(p.coin, p.icon_url || tokenIconUrl(p.coin))}
      <div><div class="row-title coin-side ${sideClass(p.side)}">${p.coin}</div><div class="row-sub">${p.side}</div></div>
      <div><div class="row-sub">Target</div><strong>${fmtUsd(p.target_notional)}</strong></div>
      <div><div class="row-sub">Actual</div><strong>${fmtUsd(p.actual_notional)}</strong></div>
      <div><div class="row-sub">Drift</div><strong class="${positiveClass(p.drift_pct)}">${fmtPct(p.drift_pct)}</strong></div>
      <div><div class="row-sub">PnL</div><strong class="${positiveClass(p.pnl)}">${fmtUsd(p.pnl)}</strong></div>
    </div>
  `).join('') : `<div class="empty-state compact-empty">No open positions yet.</div>`;

  const closeControls = isClosing || String(w.status).toLowerCase() === 'closed' ? `
    <div class="withdraw-box">
      <div>
        <div class="row-title">Withdraw funds</div>
        <div class="row-sub">Enter destination wallet and confirm withdraw + delete.</div>
      </div>
      <input id="withdrawDest_${w.id}" class="form-input" placeholder="Destination wallet 0x..." />
      <button class="danger-btn" data-withdraw-delete="${w.id}">Confirm Withdraw and Delete</button>
    </div>
  ` : `
    <button class="danger-outline-btn" data-close-copy="${w.id}">Close Copytrading</button>
  `;

  return `
    <div class="wallet-expanded">
      <div class="detail-grid wallet-detail-grid">
        <div class="detail-card"><span>Wallet value</span><strong>${fmtUsd(w.value)}</strong></div>
        <div class="detail-card"><span>Available</span><strong>${fmtUsd(w.available)}</strong></div>
        <div class="detail-card"><span>Realized PnL</span><strong class="${positiveClass(w.realized_pnl)}">${fmtUsd(w.realized_pnl)}</strong></div>
        <div class="detail-card"><span>Unrealized PnL</span><strong class="${positiveClass(w.unrealized_pnl)}">${fmtUsd(w.unrealized_pnl)}</strong></div>
      </div>
      <div class="expanded-subhead">Open positions</div>
      <div class="wallet-position-list">${positionsHtml}</div>
      <div class="wallet-close-area">${closeControls}</div>
    </div>
  `;
}

function renderMultiLeaderboard(pools, wallets) {
  const el = safeClassRemove('multiLeaderboard', 'loading');
  if (!el) return;

  const rows = (pools || []).map(pool => {
    const wallet = wallets.find(w => Number(w.pool_id) === Number(pool.id)) || wallets.find(w => Number(w.id) === Number(pool.wallet_id)) || {};
    const members = pool.members || [];
    const pnl = Number(wallet.total_pnl || 0);
    const value = Number(wallet.value || 0);
    return { pool, wallet, members, pnl, value };
  }).sort((a, b) => b.pnl - a.pnl);

  if (!rows.length) {
    el.innerHTML = `
      <div class="empty-state compact-empty">
        No multi copytrading wallets yet. Create one in the Multi Copytrading section.
      </div>
    `;
    return;
  }

  el.innerHTML = rows.map((row, i) => `
    <div class="multi-rank-row">
      <div class="rank-badge">#${i + 1}</div>
      <div>
        <div class="row-title">${row.pool.name || `Multi Copy #${row.pool.id}`}</div>
        <div class="row-sub">${row.members.length || 0} copied wallets · ${row.members.map(m => shortAddress(m.trader_address)).join(' · ')}</div>
      </div>
      <div>
        <div class="row-sub">Value</div>
        <strong>${fmtUsd(row.value)}</strong>
      </div>
      <div>
        <div class="row-sub">PnL</div>
        <strong class="${positiveClass(row.pnl)}">${fmtUsd(row.pnl)}</strong>
      </div>
      <button class="copy-btn small-copy" data-copy-multi="${row.pool.id}">Copy Vault</button>
    </div>
  `).join('');

  el.querySelectorAll('[data-copy-multi]').forEach(btn => {
    btn.addEventListener('click', () => {
      const pool = state.pools.find(p => String(p.id) === String(btn.dataset.copyMulti));
      openVaultCopySettings(pool);
    });
  });
}

function firstFreeMultiSlot() {
  return Math.min(multiSlotLimit(), multiWalletCount() + 1);
}

function renderLiveTraderFeed(positions) {
  initRandomLiveFeed();
}

function initRandomLiveFeed() {
  if (!state.liveFeedTransactions.length) {
    state.liveFeedTransactions = generateRandomFeedTransactions(50);
  }
  renderRandomLiveFeed();

  if (!state.liveFeedTimer) {
    state.liveFeedTimer = setInterval(() => {
      const next = makeRandomTrade();
      state.liveFeedTransactions.unshift(next);
      state.liveFeedTransactions = state.liveFeedTransactions.slice(0, 50);
      renderRandomLiveFeed(true);
    }, 3000);
  }
}

function renderRandomLiveFeed(animateFirst = false) {
  updateLiveFeedHeader();

  const el = safeClassRemove('liveTraderFeed', 'loading');
  if (!el) return;

  el.innerHTML = state.liveFeedTransactions.slice(0, 50).map((tx, i) => `
    <div class="trade-feed-row random-tx-row ${animateFirst && i === 0 ? 'new-tx' : ''} ${tx.pnl >= 0 ? 'tx-positive' : 'tx-negative'}">
      <div class="feed-row-icon-wrap">
        ${feedSourceLogoHtml()}
      </div>
      <div>
        <div class="row-title">${tx.name || tx.vaultName || 'Copy Wallet'}</div>
        <div class="row-sub"><span class="feed-token-inline">${coinIconHtml(tx.ticker, tokenIconUrl(tx.ticker))}</span>${tx.ticker} · ${tx.side}</div>
      </div>
      <div>
        <div class="row-sub">Size</div>
        <strong>${fmtUsd(tx.sizeUsd)}</strong>
      </div>
      <div>
        <div class="row-sub">PnL</div>
        <strong>${fmtUsd(tx.pnl)}</strong>
      </div>
    </div>
  `).join('');
}


function generateRandomFeedTransactions(count) {
  return Array.from({ length: count }, () => makeRandomTrade());
}

function makeRandomTrade() {
  const tickers = ['BTC', 'ETH', 'SOL', 'HYPE', 'DOGE', 'ARB', 'OP', 'LINK', 'AVAX', 'BNB'];
  const sides = ['Long', 'Short'];
  const names = getFeedNamesForCurrentView();
  const ticker = tickers[Math.floor(Math.random() * tickers.length)];
  const sizeUsd = randomBetween(250, 45000);
  const pnlMagnitude = randomBetween(8, Math.max(18, sizeUsd * 0.045));
  const pnl = Math.random() > 0.42 ? pnlMagnitude : -pnlMagnitude;

  return {
    name: names[Math.floor(Math.random() * names.length)],
    ticker,
    side: sides[Math.floor(Math.random() * sides.length)],
    sizeUsd,
    pnl,
    ts: Date.now(),
  };
}


function feedSourceLogoHtml() {
  const isVaultView = state.mainView === 'fatbot-vaults';
  const src = isVaultView ? '/static/assets/fatbot-logo.png' : '/static/assets/hyperliquid-logo.png';
  const fallback = isVaultView ? 'FB' : 'HL';
  return `<img class="feed-row-source-logo ${isVaultView ? 'fatbot-feed-logo' : 'hl-feed-logo'}" src="${src}" alt="${fallback}" onerror="this.style.display='none';this.parentElement.classList.add('logo-fallback');this.parentElement.dataset.fallback='${fallback}'" />`;
}

function updateLiveFeedHeader() {
  const isVaultView = state.mainView === 'fatbot-vaults';
  const title = document.getElementById('liveFeedTitle');
  const subtitle = document.getElementById('liveFeedSubtitle');
  const logo = document.getElementById('liveFeedSourceLogo');

  if (title) title.textContent = isVaultView ? 'Live FatBot Vaults trades feed' : 'Live copytrading trades feed';
  if (subtitle) subtitle.textContent = isVaultView
    ? 'Trades and activity from FatBot vault copy indexes.'
    : 'Trades and activity from single copytrading wallets.';
  if (logo) {
    logo.src = isVaultView ? '/static/assets/fatbot-logo.png' : '/static/assets/hyperliquid-logo.png';
    logo.alt = isVaultView ? 'FatBot' : 'Hyperliquid';
  }
}

function getFeedNamesForCurrentView() {
  if (state.mainView === 'fatbot-vaults') {
    const fromPools = (state.pools || []).map(p => p.name).filter(Boolean);
    const fallback = [
      'FatBot Vault #1',
      'FatBot Vault #2',
      'Momentum Alpha Vault',
      'High Conviction Vault',
      'Delta Hunter Vault',
      'Perps Growth Vault',
      'Copy Basket Vault',
      'Hyperliquid Trend Vault',
    ];
    return fromPools.length ? fromPools.concat(fallback).slice(0, 16) : fallback;
  }

  const singles = (state.wallets || [])
    .filter(w => w.mode !== 'pool')
    .map(w => w.label || shortAddress(w.copied_trader_address || w.wallet_address || ''))
    .filter(Boolean);

  const fallback = [
    'Copy Wallet #1',
    'Copy Wallet #2',
    'Single Copy Wallet',
    'HL Wallet Copy',
    'Perps Copy Wallet',
    'Smart Wallet Copy',
  ];

  return singles.length ? singles.concat(fallback).slice(0, 16) : fallback;
}


function randomBetween(min, max) {
  return Math.round((min + Math.random() * (max - min)) * 100) / 100;
}


function renderLivePositions(positions) {
  const el = safeClassRemove('livePositions', 'loading');
  if (!el) return;
  if (!positions.length) {
    el.innerHTML = `<p class="muted">No live positions yet.</p>`;
    return;
  }
  el.innerHTML = positions.slice(0, 7).map(p => `
    <div class="position-row">
      ${coinIconHtml(p.coin, p.icon_url || tokenIconUrl(p.coin))}
      <div><div class="row-title">${p.coin}</div><div class="row-sub">${p.wallet_label} · ${p.side}</div></div>
      <div><div class="row-sub">Actual</div><strong>${fmtUsd(p.actual_notional)}</strong></div>
      <div><div class="row-sub">Drift</div><strong class="${positiveClass(p.drift_pct)}">${fmtPct(p.drift_pct)}</strong></div>
      <div><div class="row-sub">PnL</div><strong class="${positiveClass(p.pnl)}">${fmtUsd(p.pnl)}</strong></div>
      <div><div class="row-sub">PnL %</div><strong class="${positiveClass(p.pnl_pct)}">${fmtPct(p.pnl_pct)}</strong></div>
    </div>
  `).join('');
}

function renderMoves(positions) {
  const el = $('movesList');
  if (!el) return;
  const items = positions.slice(0, 3);
  el.innerHTML = items.map(p => `
    <div class="move-row">
      <span>${p.coin} ${String(p.side || '').toLowerCase()} copied</span>
      <strong class="${positiveClass(p.pnl)}">${fmtUsd(p.pnl)}</strong>
    </div>
  `).join('') || `
    <div class="move-row"><span>No recent execution moves.</span><strong>$0.00</strong></div>
  `;
}

async function openTrader(address) {
  const el = document.getElementById('traderModalContent');

  const preview = [...(state.traders || []), ...(state.fatbotVaults || [])].find(t => String(t.address || '').toLowerCase() === String(address || '').toLowerCase());
  const previewTitle = preview && preview.source === 'fatbot_vault'
    ? (preview.label || shortAddress(address))
    : shortAddress(address);

  el.innerHTML = `
    <div class="wizard-head trader-profile-head">
      <div>
        <span class="pill">TRADER PROFILE</span>
        <div style="display:flex; align-items:center; gap:12px; margin-top:10px;">
          ${preview ? leaderLogoHtml(preview, 0, 'profile-provider-logo') : `<div class="avatar-badge alt-a">${traderBadgeLabel(address)}</div>`}
          <div>
            <h2 style="margin:0;">${previewTitle}</h2>
          </div>
        </div>
      </div>
      <button class="primary trader-head-copy" data-modal-copy="${address}">COPY THIS TRADER</button>
    </div>
    <div class="profile-loading-card">
      <div class="mini-spinner"></div>
      <div>
        <strong>Loading live profile...</strong>
        <p class="muted">Fetching cached leaderboard data and Hyperliquid live state.</p>
      </div>
    </div>
  `;

  el.querySelector('[data-modal-copy]').addEventListener('click', () => {
    closeModal('traderModal');
    openCopyWizard(address);
  });
  openModal('traderModal');

  let trader;
  try {
    trader = await api(`/api/traders/${encodeURIComponent(address)}?${leaderboardQueryString()}`);
  } catch (err) {
    el.innerHTML += `<div class="empty-state">Failed to load trader profile: ${err.message || err}</div>`;
    return;
  }

  state.selectedTrader = trader;
  const isLive = isHydro(trader) || trader.source === 'fatbot_vault';
  const positions = trader.positions || [];

  const liveCards = isLive ? `
      <div class="detail-card"><span>${trader.source === "fatbot_vault" ? `${String((state.leaderboardFilters || {}).window || "30d").toUpperCase()} PnL` : `PnL Window (${String((state.leaderboardFilters || {}).window || "30d").toUpperCase()})`}</span><strong class="${positiveClass(trader.source === "fatbot_vault" ? (trader.pnl_pct ?? trader.pnl_30d) : trader.total_pnl)}">${trader.source === "fatbot_vault" ? fmtPct(trader.pnl_pct ?? trader.pnl_30d ?? 0) : fmtUsd(trader.total_pnl || 0)}</strong></div>
      <div class="detail-card"><span>Account Value</span><strong>${moneyOrDash(trader.account_value)}</strong></div>
      <div class="detail-card"><span>Long / Short</span><strong>${exposureShareDisplay(trader)}</strong></div>
      <div class="detail-card"><span>Gross Exposure</span><strong>${grossExposureDisplay(trader)}</strong></div>
      <div class="detail-card"><span>Win Rate</span><strong>${winRateDisplay(trader)}</strong></div>
      <div class="detail-card"><span>Total Trades</span><strong>${Number(trader.total_trades || trader.trades || 0).toLocaleString()}</strong></div>
      <div class="detail-card"><span>Account Age</span><strong>${Number(trader.account_age_days || 0)} days</strong></div>
      <div class="detail-card"><span>Volume</span><strong>${fmtUsd(trader.volume || trader.volume_traded || 0)}</strong></div>
      <div class="detail-card"><span>Total Funding</span><strong class="${positiveClass(trader.total_funding || trader.funding)}">${moneyOrDash(trader.total_funding || trader.funding)}</strong></div>
      <div class="detail-card"><span>Live Positions</span><strong>${Number(trader.open_positions || 0)}</strong></div>
  ` : `
      <div class="detail-card"><span>30D PnL</span><strong class="${positiveClass(trader.pnl_30d)}">${fmtPct(trader.pnl_30d)}</strong></div>
      <div class="detail-card"><span>90D PnL</span><strong class="${positiveClass(trader.pnl_90d)}">${fmtPct(trader.pnl_90d)}</strong></div>
      <div class="detail-card"><span>Volume</span><strong>${fmtUsd(trader.volume || 0)}</strong></div>
      <div class="detail-card"><span>Open Positions</span><strong>${trader.open_positions || 0}</strong></div>
      <div class="detail-card"><span>Win Rate</span><strong>${winRateDisplay(trader)}</strong></div>
  `;

  el.innerHTML = `
    <div class="wizard-head trader-profile-head">
      <div>
        <span class="pill">TRADER PROFILE</span>
        <div style="display:flex; align-items:center; gap:12px; margin-top:10px;">
          ${leaderLogoHtml(trader, 0, 'profile-provider-logo')}
          <div>
            <h2 style="margin:0;">${trader.source === 'fatbot_vault' ? (trader.label || shortAddress(trader.address)) : shortAddress(trader.address)}</h2>
            ${isLive ? '' : `<p>${trader.label}</p>`}
          </div>
        </div>
      </div>
      <button class="primary trader-head-copy" data-modal-copy="${trader.address}">COPY THIS TRADER</button>
    </div>

    <div class="detail-grid hydro-detail-grid">
      ${liveCards}
    </div>

    <div class="panel-head small" style="margin-top:18px;">
      <h3>${isLive ? 'Live Hyperliquid positions' : 'Open positions'}</h3>
    </div>

    <div class="position-list">
      ${positions.length ? positions.map(p => `
        <div class="position-row trader-live-position-row">
          ${coinIconHtml(p.coin, p.icon_url)}
          <div><div class="row-title coin-side ${sideClass(p.side)}">${p.coin}</div><div class="row-sub">${p.side} · ${Number(p.leverage || 0).toFixed(1)}x</div></div>
          <div><div class="row-sub">Notional</div><strong>${fmtUsd(p.notional)}</strong></div>
          <div><div class="row-sub">Entry</div><strong>${p.entry ? Number(p.entry).toLocaleString(undefined, { maximumFractionDigits: 6 }) : "—"}</strong></div>
          <div><div class="row-sub">Live Price</div><strong>${(p.live_price || p.display_price) ? Number(p.live_price || p.display_price).toLocaleString(undefined, { maximumFractionDigits: 6 }) : "—"}</strong></div>
          <div><div class="row-sub">PnL</div><strong class="${positiveClass(p.pnl)}">${fmtUsd(p.pnl)}</strong></div>
          <div><div class="row-sub">Liq</div><strong>${p.liq_price ? Number(p.liq_price).toLocaleString() : '—'}</strong></div>
        </div>
      `).join('') : `<p class="muted">${isLive ? 'No current open Hyperliquid positions for this wallet. Current long/short and gross exposure are therefore 0.' : 'No live positions available for this trader yet.'}</p>`}
    </div>
  `;

  el.querySelector('[data-modal-copy]').addEventListener('click', () => {
    closeModal('traderModal');
    openCopyWizard(trader.address);
  });
}


function openSlotSettings(mode, slot) {
  state.copySetupMode = mode;
  state.selectedSlot = slot;
  state.wizardStep = 0;
  state.generatedWallet = null;

  if (mode === 'single') {
    state.singleWalletName = '';
    const singleCount = singleWalletCount();
    if (singleCount >= singleSlotLimit()) {
      showSingleSlotsFullAlert();
      return;
    }
    state.selectedTrader = state.traders[0] || { address: '' };
    state.selectedMultiTraders = [];
    document.getElementById('copyModalTrader').textContent = `Single Copytrading · Slot #${slot}`;
  } else {
    const multiCount = multiWalletCount();
    if (multiCount >= multiSlotLimit()) {
      showMultiSlotsFullAlert();
      return;
    }
    state.selectedTrader = null;
    if (!state.vaultName) state.vaultName = `FatBot Vault #${slot}`;
    if (!state.selectedMultiTraders || state.selectedMultiTraders.length === 0) {
      state.selectedMultiTraders = state.traders.slice(0, 5).map(t => t.address);
    }
    document.getElementById('copyModalTrader').textContent = `FatBot Vaults · Slot #${slot}`;
  }

  renderWizard();
  openModal('copyModal');
}




function singleWalletCount() {
  return state.wallets.filter(w => w.mode !== 'pool').length;
}

function multiWalletCount() {
  return state.wallets.filter(w => w.mode === 'pool').length;
}

function showSingleSlotsFullAlert() {
  alert(`Single Copytrading slots are full: ${singleSlotLimit()}/${singleSlotLimit()}. Close or delete one single copytrading wallet before creating another one.`);
}

function showMultiSlotsFullAlert() {
  alert(`FatBot Vault slots are full: ${multiSlotLimit()}/${multiSlotLimit()}. Close or delete one FatBot Vault before creating another one.`);
}

function openVaultCopySettings(pool) {
  if (singleWalletCount() >= singleSlotLimit()) {
    showSingleSlotsFullAlert();
    return;
  }
  state.copySetupMode = 'vault_single';
  state.selectedVaultToCopy = pool;
  state.selectedSlot = firstFreeSingleSlot();
  state.wizardStep = 0;
  state.generatedWallet = null;
  state.vaultName = `Copy of ${pool?.name || 'Multi Vault'}`;
  state.selectedTrader = {
    address: `vault:${pool?.id || 'unknown'}`,
    label: pool?.name || 'Multi Vault',
  };

  document.getElementById('copyModalTrader').textContent = `${pool?.name || 'Multi Vault'} · Single Wallet Copy`;
  renderWizard();
  openModal('copyModal');
}

function firstFreeSingleSlot() {
  return Math.min(singleSlotLimit(), singleWalletCount() + 1);
}

function openCopyWizard(address) {
  const singleCount = state.wallets.filter(w => w.mode !== 'pool').length;
  if (singleCount >= singleSlotLimit()) {
    alert('Maximum 5 single copytrading wallets allowed.');
    return;
  }

  state.copySetupMode = 'single';
  state.selectedSlot = null;
  state.selectedMultiTraders = [];
  state.vaultName = '';
  state.selectedTrader = [...state.traders, ...state.fatbotVaults].find(t => t.address === address) || { address };
  state.wizardStep = 0;
  state.generatedWallet = null;
  document.getElementById('copyModalTrader').textContent = `Copying selected trader: ${shortAddress(address)}`;
  renderWizard();
  openModal('copyModal');
}

function renderWizard() {
  const step = state.wizardStep;
  const el = document.getElementById('wizardStep');
  const next = document.getElementById('wizardNext');
  const back = document.getElementById('wizardBack');
  const isMulti = state.copySetupMode === 'multi';
  back.style.visibility = step === 0 ? 'hidden' : 'visible';

  if (step === 0) {
    next.textContent = state.copySetupMode === 'vault_single' ? 'Copy Vault' : (isMulti ? 'Create FatBot Vault' : 'Create Single Wallet');

    if (state.copySetupMode === 'vault_single') {
      const pool = state.selectedVaultToCopy;
      const members = (pool?.members || []).map(m => m.trader_address).slice(0, 5);
      el.innerHTML = `
        <h3>Step 1: Copy vault settings</h3>
        <p class="muted">This creates one user copy wallet in Single Copytrading. The source is the selected multi vault.</p>
        <div class="detail-grid">
          <div class="detail-card"><span>Mode</span><strong>Single Wallet Copy</strong></div>
          <div class="detail-card"><span>Slot</span><strong>#${state.selectedSlot || 1}</strong></div>
        </div>
        <div class="selected-vault-card">
          <div>
            <div class="row-title">${pool?.name || 'Multi Vault'}</div>
            <div class="row-sub">${members.length} source wallets · ${members.map(shortAddress).join(' · ')}</div>
          </div>
        </div>
        ${rangeRow('Copy multiplier', 'multiplier', 0.1, 10, 0.1, 'x')}
        ${drawdownRow()}
        ${marginInfoRow()}
        ${numberRow('Max gross exposure', 'max_gross_exposure_pct', '%')}
      `;
      bindWizardInputs();
      return;
    }

    if (isMulti) {
      el.innerHTML = `
        <h3>Step 1: FatBot Vault settings</h3>
        <p class="muted">Select up to 5 leaderboard wallets or add your own wallet address.</p>
        <div class="detail-grid">
          <div class="detail-card"><span>Mode</span><strong>FatBot Vault</strong></div>
          <div class="detail-card"><span>Slot</span><strong>#${state.selectedSlot || 1}</strong></div>
        </div>
        ${vaultNameRow()}
        ${multiWalletPicker()}
        ${rangeRow('Copy multiplier', 'multiplier', 0.1, 10, 0.1, 'x')}
        ${drawdownRow()}
        ${marginInfoRow()}
        ${numberRow('Max gross exposure', 'max_gross_exposure_pct', '%')}
      `;
      bindWizardInputs();
      bindVaultName();
      bindMultiWalletPicker();
      return;
    }

    el.innerHTML = `
      <h3>Step 1: Single copy settings</h3>
      <p class="muted">Choose one leaderboard wallet or add your own wallet address.</p>
      <div class="detail-grid">
        <div class="detail-card"><span>Mode</span><strong>Single Trader Copy</strong></div>
        <div class="detail-card"><span>Slot</span><strong>#${state.selectedSlot || 'direct'}</strong></div>
      </div>
      ${singleWalletNameRow()}
      ${traderSelectRow()}
      ${customSingleWalletRow()}
      ${rangeRow('Copy multiplier', 'multiplier', 0.1, 10, 0.1, 'x')}
      ${drawdownRow()}
      ${marginInfoRow()}
      ${numberRow('Max gross exposure', 'max_gross_exposure_pct', '%')}
    `;
    bindWizardInputs();
    bindSingleWalletName();
    bindTraderSelect();
    bindCustomSingleWallet();
  }

  if (step === 1) {
    next.textContent = 'Continue';
    el.innerHTML = `
      <h3>Step 2: Fund wallet</h3>
      <p class="muted">Deposit USDC to generated wallet address. For MVP you can continue without live funding.</p>
      <div class="address-box">${state.generatedWallet.wallet_address}</div>
      <div class="detail-grid">
        <div class="detail-card"><span>Detected Balance</span><strong>$0.00</strong></div>
        <div class="detail-card"><span>Status</span><strong>${String(state.generatedWallet.status || '').toUpperCase()}</strong></div>
      </div>
    `;
  }

  if (step === 2) {
    next.textContent = 'Activate Copy Wallet';
    el.innerHTML = `
      <h3>Step 3: Activate</h3>
      <p class="muted">Activate the wallet and seed demo target positions for the dashboard preview.</p>
      <div class="detail-grid">
        <div class="detail-card"><span>Wallet</span><strong>${state.generatedWallet.wallet_address}</strong></div>
        <div class="detail-card"><span>Copy multiplier</span><strong>${state.wizardSettings.multiplier}x</strong></div>
        <div class="detail-card"><span>Max drawdown</span><strong>${Math.abs(state.wizardSettings.stop_drawdown_pct)}%</strong></div>
        <div class="detail-card"><span>Max gross exposure</span><strong>${state.wizardSettings.max_gross_exposure_pct}%</strong></div>
      </div>
    `;
  }

  if (step === 3) {
    next.textContent = 'Close';
    el.innerHTML = `
      <h3>Wallet created</h3>
      <p class="muted">Your copy wallet is now visible in the dashboard.</p>
      <div class="address-box">${state.generatedWallet.wallet_address}</div>
    `;
  }
}


function singleWalletNameRow() {
  return `
    <div class="form-row">
      <label>Name this copy wallet</label>
      <input id="singleWalletName" class="form-input" placeholder="Optional, e.g. My BTC Copy Wallet" value="${state.singleWalletName || ''}" />
      <small class="muted">Optional. If empty, the wallet name stays as the copied wallet address.</small>
    </div>
  `;
}

function bindSingleWalletName() {
  const input = document.getElementById('singleWalletName');
  if (!input) return;
  input.addEventListener('input', () => {
    state.singleWalletName = input.value;
  });
}

function traderSelectRow() {
  const options = state.traders.map((t, i) => `
    <option value="${t.address}" ${state.selectedTrader && state.selectedTrader.address === t.address ? 'selected' : ''}>
      #${i + 1} ${shortAddress(t.address)} · ${t.source === 'hydromancer' ? fmtUsd(t.total_pnl) : fmtPct(t.pnl_30d)}
    </option>
  `).join('');

  return `
    <div class="form-row">
      <label>Select leaderboard wallet</label>
      <select id="wizardTraderSelect" class="form-select">
        ${options}
      </select>
      <small class="muted">Or paste a custom wallet address below.</small>
    </div>
  `;
}

function customSingleWalletRow() {
  return `
    <div class="form-row">
      <label>Add your own wallet</label>
      <div class="inline-wallet-add">
        <input id="customSingleWallet" class="form-input" placeholder="0x..." />
        <button id="useCustomSingleWallet" class="secondary" type="button">Use wallet</button>
      </div>
      <small class="muted">Custom wallet will override the selected leaderboard wallet for this single copy slot.</small>
    </div>
  `;
}


function vaultNameRow() {
  return `
    <div class="form-row">
      <label>Vault name</label>
      <input id="vaultNameInput" class="form-input" value="${state.vaultName || `Multi Vault #${state.selectedSlot || 1}`}" placeholder="e.g. Momentum Alpha Vault" />
      <small class="muted">This name will be shown in the Multi Copytrading leaderboard and live feed.</small>
    </div>
  `;
}

function bindVaultName() {
  const input = document.getElementById('vaultNameInput');
  if (!input) return;
  input.addEventListener('input', () => {
    state.vaultName = input.value.trim();
  });
}

function multiWalletPicker() {
  const rows = state.traders.slice(0, 12).map((t, i) => {
    const checked = state.selectedMultiTraders.includes(t.address) ? 'checked' : '';
    return `
      <label class="wallet-choice-row">
        <input type="checkbox" data-multi-wallet="${t.address}" ${checked} />
        <span class="slot-index">${i + 1}</span>
        <strong>${shortAddress(t.address)}</strong>
        <em>${t.source === 'hydromancer' ? fmtUsd(t.total_pnl) : fmtPct(t.pnl_30d)}</em>
      </label>
    `;
  }).join('');

  const selectedCustomRows = state.selectedMultiTraders
    .filter(addr => !state.traders.some(t => t.address === addr))
    .map(addr => `
      <div class="wallet-choice-row custom-selected-wallet">
        <span class="slot-index">+</span>
        <strong>${shortAddress(addr)}</strong>
        <em>Custom wallet</em>
      </div>
    `).join('');

  return `
    <div class="form-row">
      <label>Select up to 5 wallets</label>
      <div class="wallet-choice-list">
        ${rows}
        ${selectedCustomRows}
      </div>
      <div class="inline-wallet-add">
        <input id="customMultiWallet" class="form-input" placeholder="Add your own wallet 0x..." />
        <button id="addCustomMultiWallet" class="secondary" type="button">Add wallet</button>
      </div>
      <small class="muted">Selected: <strong id="multiSelectedCount">${state.selectedMultiTraders.length}</strong> / 5</small>
    </div>
  `;
}

function bindTraderSelect() {
  const select = document.getElementById('wizardTraderSelect');
  if (!select) return;
  select.addEventListener('change', () => {
    state.selectedTrader = state.traders.find(t => t.address === select.value) || { address: select.value };
  });
}

function bindCustomSingleWallet() {
  const input = document.getElementById('customSingleWallet');
  const btn = document.getElementById('useCustomSingleWallet');
  if (!input || !btn) return;

  btn.addEventListener('click', () => {
    const value = input.value.trim();
    if (!isValidWallet(value)) {
      alert('Enter a valid wallet address starting with 0x.');
      return;
    }
    state.selectedTrader = { address: value, label: 'Custom wallet' };
    const select = document.getElementById('wizardTraderSelect');
    if (select) select.value = '';
    input.value = value;
  });
}

function bindMultiWalletPicker() {
  document.querySelectorAll('[data-multi-wallet]').forEach(input => {
    input.addEventListener('change', () => {
      const addr = input.dataset.multiWallet;
      if (input.checked) {
        if (state.selectedMultiTraders.length >= 5) {
          input.checked = false;
          alert('You can select maximum 5 wallets.');
          return;
        }
        if (!state.selectedMultiTraders.includes(addr)) state.selectedMultiTraders.push(addr);
      } else {
        state.selectedMultiTraders = state.selectedMultiTraders.filter(x => x !== addr);
      }
      const count = document.getElementById('multiSelectedCount');
      if (count) count.textContent = state.selectedMultiTraders.length;
    });
  });

  const customInput = document.getElementById('customMultiWallet');
  const customBtn = document.getElementById('addCustomMultiWallet');
  if (!customInput || !customBtn) return;

  customBtn.addEventListener('click', () => {
    const value = customInput.value.trim();
    if (!isValidWallet(value)) {
      alert('Enter a valid wallet address starting with 0x.');
      return;
    }
    if (state.selectedMultiTraders.length >= 5) {
      alert('You can select maximum 5 wallets.');
      return;
    }
    if (!state.selectedMultiTraders.includes(value)) state.selectedMultiTraders.push(value);
    renderWizard();
  });
}

function isValidWallet(value) {
  return /^0x[a-fA-F0-9]{8,}$/.test(value);
}

function drawdownRow() {
  return `
    <div class="form-row">
      <label>Max drawdown: <strong id="drawdownLabel">${Math.abs(state.wizardSettings.stop_drawdown_pct)}%</strong></label>
      <input type="range" data-drawdown-setting="stop_drawdown_pct" min="1" max="95" step="1" value="${Math.abs(state.wizardSettings.stop_drawdown_pct)}">
      <small class="muted">Stops the bot if wallet value falls this much from its maximum.</small>
    </div>
  `;
}

function marginInfoRow() {
  return `
    <div class="readonly-info-row">
      <span>Margin mode</span>
      <strong>Cross</strong>
      <em>Cannot be changed in this setup.</em>
    </div>
  `;
}


function rangeRow(label, key, min, max, step, suffix) {
  return `
    <div class="form-row">
      <label>${label}: <strong id="${key}Label">${state.wizardSettings[key]}${suffix}</strong></label>
      <input type="range" data-setting="${key}" min="${min}" max="${max}" step="${step}" value="${state.wizardSettings[key]}">
    </div>
  `;
}

function numberRow(label, key, suffix) {
  return `
    <div class="form-row">
      <label>${label}</label>
      <input type="number" data-setting="${key}" value="${state.wizardSettings[key]}">
      <small class="muted">Current: ${state.wizardSettings[key]}${suffix}</small>
    </div>
  `;
}

function bindWizardInputs() {
  document.querySelectorAll('[data-setting]').forEach(input => {
    input.addEventListener('input', () => {
      state.wizardSettings[input.dataset.setting] = Number(input.value);
      const label = document.getElementById(`${input.dataset.setting}Label`);
      if (label) label.textContent = `${input.value}x`;
    });
  });

  document.querySelectorAll('[data-drawdown-setting]').forEach(input => {
    input.addEventListener('input', () => {
      state.wizardSettings.stop_drawdown_pct = -Math.abs(Number(input.value));
      const label = document.getElementById('drawdownLabel');
      if (label) label.textContent = `${Math.abs(state.wizardSettings.stop_drawdown_pct)}%`;
    });
  });
}

async function nextWizard() {
  if (state.isCreatingCopy) return;
  state.isCreatingCopy = true;

  const nextBtn = document.getElementById('wizardNext');
  const originalText = nextBtn ? nextBtn.textContent : '';
  if (nextBtn) {
    nextBtn.disabled = true;
    nextBtn.textContent = 'Creating...';
  }

  try {
    const isMulti = state.copySetupMode === 'multi';
    const isVaultSingle = state.copySetupMode === 'vault_single';

    if (state.wizardStep === 0) {
      if (isMulti) {
        if (multiWalletCount() >= multiSlotLimit()) {
          showMultiSlotsFullAlert();
          return;
        }
        const selected = state.selectedMultiTraders.slice(0, 5);
        if (selected.length < 2) {
          alert('Select at least 2 wallets for multi copytrading.');
          return;
        }

        const pool = await api('/api/pools', {
          method: 'POST',
          body: JSON.stringify({
            name: state.vaultName || `FatBot Vault #${state.selectedSlot || 1}`,
            vault_name: state.vaultName || `FatBot Vault #${state.selectedSlot || 1}`,
            trader_addresses: selected,
            multiplier: state.wizardSettings.multiplier,
          }),
        });

        if (pool.wallet_id) {
          await api(`/api/wallets/${pool.wallet_id}/settings`, {
            method: 'PATCH',
            body: JSON.stringify(state.wizardSettings),
          });
          await api(`/api/wallets/${pool.wallet_id}/activate`, { method: 'POST' });
        }

        await loadAll();
        closeModal('copyModal');
        return;
      }

      if (isVaultSingle) {
        if (singleWalletCount() >= singleSlotLimit()) {
          showSingleSlotsFullAlert();
          return;
        }
        const pool = state.selectedVaultToCopy;
        if (!pool) {
          alert('Select a vault first.');
          return;
        }

        const wallet = await api('/api/wallets/generate', {
          method: 'POST',
          body: JSON.stringify({
            mode: 'single',
            trader_address: `vault:${pool.id}`,
            label: `Single Slot #${state.selectedSlot || 1} · Copy of ${pool.name || 'Multi Vault'}`,
          }),
        });

        await api(`/api/wallets/${wallet.id}/settings`, {
          method: 'PATCH',
          body: JSON.stringify(state.wizardSettings),
        });
        await api(`/api/wallets/${wallet.id}/activate`, { method: 'POST' });

        await loadAll();
        closeModal('copyModal');
        return;
      }

      if (singleWalletCount() >= singleSlotLimit()) {
        showSingleSlotsFullAlert();
        return;
      }

      if (!state.selectedTrader || !state.selectedTrader.address) {
        alert('Select a trader first.');
        return;
      }

      const singleName = String(state.singleWalletName || '').trim();
      const defaultSingleName = shortAddress(state.selectedTrader.address);
      const wallet = await api('/api/wallets/generate', {
        method: 'POST',
        body: JSON.stringify({
          mode: 'single',
          trader_address: state.selectedTrader.address,
          label: singleName || defaultSingleName,
        }),
      });

      await api(`/api/wallets/${wallet.id}/settings`, {
        method: 'PATCH',
        body: JSON.stringify(state.wizardSettings),
      });
      await api(`/api/wallets/${wallet.id}/activate`, { method: 'POST' });

      await loadAll();
      closeModal('copyModal');
      return;
    }

    closeModal('copyModal');
  } catch (err) {
    console.error(err);
    alert(`Create failed: ${err.message || err}`);
  } finally {
    state.isCreatingCopy = false;
    if (nextBtn) {
      nextBtn.disabled = false;
      nextBtn.textContent = originalText || (
        state.copySetupMode === 'vault_single'
          ? 'Copy Vault'
          : (state.copySetupMode === 'multi' ? 'Create FatBot Vault' : 'Create Single Wallet')
      );
    }
  }
}

function backWizard() {
  state.wizardStep = Math.max(0, state.wizardStep - 1);
  renderWizard();
}

function openModal(id) { document.getElementById(id).classList.remove('hidden'); }
function closeModal(id) { document.getElementById(id).classList.add('hidden'); }

function bindMainNavigation() {
  document.querySelectorAll('[data-main-view]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-main-view]').forEach(x => x.classList.remove('active'));
      btn.classList.add('active');
      state.mainView = btn.dataset.mainView === 'fatbot-vaults' ? 'fatbot-vaults' : 'copytrading';
      renderCopySections(state.wallets || []);
      state.liveFeedTransactions = generateRandomFeedTransactions(50);
      renderRandomLiveFeed();
    });
  });
}

document.addEventListener('click', (e) => {
  if (e.target.dataset.close) closeModal(e.target.dataset.close);
});

document.querySelectorAll('[data-leader-tab]').forEach(btn => {
  btn.addEventListener('click', () => {
    state.activeLeaderTab = btn.dataset.leaderTab;
    renderLeaderboardTabs();
    renderTraders();
  });
});

const wizardNextBtn = document.getElementById('wizardNext');
const wizardBackBtn = document.getElementById('wizardBack');
if (wizardNextBtn) wizardNextBtn.addEventListener('click', nextWizard);
if (wizardBackBtn) wizardBackBtn.addEventListener('click', backWizard);

bindMainNavigation();
bindLeaderboardFilters();
readLeaderboardFiltersFromDom();

loadAll().catch(err => {
  console.error(err);
  document.body.insertAdjacentHTML('afterbegin', `<div style="background:#ff657f;color:white;padding:12px;text-align:center;font-weight:900">API error: ${err.message}</div>`);
});


function renderTargets() { /* removed in v9 */ }

