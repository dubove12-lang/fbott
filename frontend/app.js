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
  howItWorksIndex: 0,
  selectedSlot: null,
  activeVaultBuilderSlot: null,
  vaultBuilderStep: 0,
  defaultVaultModalTab: 'stats',
  defaultVaultMembers: JSON.parse(localStorage.getItem('fatbot_default_vault_members') || '[]'),
  vaultMemberOverrides: JSON.parse(localStorage.getItem('fatbot_vault_member_overrides') || '{}'),
  closedVaults: new Set(JSON.parse(localStorage.getItem('fatbot_closed_vaults') || '[]')),
  closeVaultDialogOpen: false,
  closeVaultWithdrawAddress: '',
  closeVaultConfirmArmed: false,
  activeSingleCopyWallet: null,
  singleCopyCloseDialogOpen: false,
  singleCopyCloseWithdrawAddress: '',
  singleCopyCloseConfirmArmed: false,
  activeLeaderTab: 'trades',
  leaderboardSnapshotStatus: null,
  leaderboardFilters: {
    window: '30d',
    sortBy: 'totalPnl',
    minTrades: 0,
    minDaysActive: 0,
    limit: 50,
    marketType: 'all',
  },
  favourites: new Set(JSON.parse(localStorage.getItem('fatbot_copy_favourites') || '[]')),
  walletAliases: JSON.parse(localStorage.getItem('fatbot_wallet_aliases') || '{}'),
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

// Manual FatBot Selection list.
// Add wallet addresses here later, lower/upper-case both work.
const FATBOT_SELECTION_ADDRESSES = [
  '0x023a3d058020fb76cca98f01b3c48c8938a22355',
  '0xc926ddba8b7617dbc65712f20cf8e1b58b8598d3',
  '0x31DEA2516BEEE92135B96F464EEEC3CF292A13F2',
  '0x9DB82C502472D76742FDD69609DFCC6E01327401',
  '0x95FDE6CF0d305078B7EEaC44182A931c169DD947',
  '0x0C87080E84Ad8e91F54c4aF0AA921e1F183d601B',
  '0xb39766100347e1ffa1459492c85e8E3a2b25d3a0',
  '0xb3162a3C788399D9EC236c67A5af083dD78c8022',
  '0xA1b6D8EfbcB2fB750a84Dbc05649fA4968034F04',
  '0x6417da1D2452a4b4A81aa151b7235fFec865082f',
  '0x47807D3f6Ae34fF6aA1fc8Fe4e7B742197C1E125',
  '0x4DEc0A851849056E259128464EF28cE78aFa27F6',
  '0xa5Fd942D4bAdBab4FE84a9E10F565dd40d5f15Ff',
  '0x7a6d5fc57f6906f337c48fe2763c3a501304f79c',
  '0x13640f452a56aaa7a5a5e5a6bd24c45374dacbcc',
  '0x63d417a577b50c96f4f09148d4e4d70950db0522',
  '0x4ba1d152409f43ad92ba358886fe94bae4f5f656',
  '0xe8681168f59af16c60c805dab7842eb75f127879',
  '0x782e432267376f377585fc78092d998f8442ab83',
  '0x44c9c226cdfae773002b3f86d3966af3cd8f277c',
  '0x054a01da80ee37d5220af5471b1eedbdcd2cdb2f',
  '0x288ed4efc8fbd1e42a06fe083ea942d20c90b336',
  '0x309eE31b6986B4a04Abbfca79A80ADa94508e1dD',
  '0x4101CE19Ee81F24da894976E585f1E79119dBD93',
  '0x7f15F9E8f49c07Ab33D4DBd05a92DbD6dfd686ab',
  '0x223537ac9a856c31f4043e86ced86bb29f06653e',
  '0x727956612a8700627451204a3ae26268bd1a1525',
  '0x365e0c115f1ca1adcb42fd21142873493df7f880',
  '0xc6d7fdfbcb55d6cad6570c5838de394d2aa24015',
  '0x09f2b610f85a5fea4d35b42cccdc52f1f71d6bc7',
  '0x1643e9aba4fcfb4e8c1a887090239e34f488cad6',
  '0xf97ad6704baec104d00b88e0c157e2b7b3a1ddd1',
  '0x02fbbf39d1e3c142994b383af5ac3f2ad744cda9',
  '0xba939edf38c0ae0cc689c98b492e0535f43e4550',
  '0x7ab12f7a0925ef24927343d47199e75a91fc78aa',
  '0x7786498ffb58bedc6c392a4a40789be5c2da240d',
  '0x5559da6ec434c5723d0ce9c4da7f29e3f8a3d43b',
  '0x5f94a51948d2376ad34a6fadfa2544e651b74b96',
  '0x2d99fe0f36c1aebd28a1a2c0e82e8ca13c2ea351'
];

function normalizedSelectionSet() {
  return new Set(FATBOT_SELECTION_ADDRESSES.map(x => String(x || '').toLowerCase()).filter(Boolean));
}

function pnlSortDesc(a, b) {
  return pnlUsdValue(b) - pnlUsdValue(a);
}

function rowLongShare(t) {
  return Number(t?.long_exposure_share_pct ?? t?.long_exposure_pct ?? 0);
}

function rowShortShare(t) {
  return Number(t?.short_exposure_share_pct ?? t?.short_exposure_pct ?? 0);
}

function rowHasOpenPositions(t) {
  return Number(t?.open_positions || 0) > 0 || (Array.isArray(t?.positions) && t.positions.length > 0);
}

function categoryMarketType(tab) {
  if (tab === 'tradfi') return 'tradfi';
  if (tab === 'crypto') return 'crypto';
  return 'all';
}


const fmtUsd = (v) => Number(v || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 });
const fmtPct = (v) => `${Number(v || 0) > 0 ? '+' : ''}${Number(v || 0).toFixed(1)}%`;
const shortAddress = (s) => (s && s.length > 12 ? `${s.slice(0, 8)}...${s.slice(-4)}` : (s || ''));
const positiveClass = (v) => (Number(v || 0) >= 0 ? 'positive' : 'negative');
function sideClass(side) {
  return String(side || '').toLowerCase().includes('short') ? 'short-side' : 'long-side';
}

function isHydro(t) {
  return t && (t.source === 'hydromancer' || t.source === 'fatbot_selection');
}
function pnlUsdValue(t) {
  if (!t) return 0;

  if (t.source === 'fatbot_vault') {
    // FatBot Vault rows already carry real USD PnL where available.
    // Do not use pnl_pct for display if we want a unified USD column.
    return Number(
      t.pnl ??
      t.total_pnl ??
      t.pnl_usd ??
      t.pnl_30d_usd ??
      t.pnl_30d ??
      0
    );
  }

  if (isHydro(t)) return Number(t.total_pnl || 0);
  return Number(t.total_pnl ?? t.pnl ?? t.pnl_30d ?? 0);
}

function pnlDisplay(t) {
  return fmtUsd(pnlUsdValue(t));
}

function pnlNumber(t) {
  return pnlUsdValue(t);
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

function fmtLivePrice(v) {
  const n = Number(v);
  if (!Number.isFinite(n)) return '—';
  if (Math.abs(n) >= 1000) return n.toLocaleString('en-US', { maximumFractionDigits: 2 });
  if (Math.abs(n) >= 100) return n.toLocaleString('en-US', { maximumFractionDigits: 3 });
  if (Math.abs(n) >= 1) return n.toLocaleString('en-US', { maximumFractionDigits: 4 });
  return n.toLocaleString('en-US', { maximumFractionDigits: 6 });
}

function statusPulseDotHtml(status) {
  const normalized = String(status || '').toLowerCase();
  return `<div class="vault-status-dot-wrap ${normalized}" title="${String(status || '').toUpperCase()}"><span class="vault-status-dot ${normalized}"></span></div>`;
}



function normalizeAddressKey(address) {
  return String(address || '').toLowerCase();
}

function saveWalletAliases() {
  localStorage.setItem('fatbot_wallet_aliases', JSON.stringify(state.walletAliases || {}));
}

function walletDisplayName(itemOrAddress) {
  const address = typeof itemOrAddress === 'string' ? itemOrAddress : (itemOrAddress?.address || itemOrAddress?.vault_id || '');
  const key = normalizeAddressKey(address);
  const alias = (state.walletAliases || {})[key];
  if (alias && String(alias).trim()) return String(alias).trim();
  if (typeof itemOrAddress === 'object' && itemOrAddress?.source === 'fatbot_vault') return itemOrAddress.label || shortAddress(address);
  return shortAddress(address);
}

function renameWalletAlias(address) {
  const key = normalizeAddressKey(address);
  if (!key) return;
  const current = (state.walletAliases || {})[key] || '';
  const next = window.prompt('Zadaj prezývku pre walletku:', current);
  if (next === null) return;
  const clean = String(next || '').trim();
  if (!state.walletAliases) state.walletAliases = {};
  if (clean) state.walletAliases[key] = clean;
  else delete state.walletAliases[key];
  saveWalletAliases();
  renderTraders();
}


function externalLinkIconSvg() {
  return `
    <svg class="external-link-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M14 5h5v5"></path>
      <path d="M10 14 19 5"></path>
      <path d="M19 14v4.5A1.5 1.5 0 0 1 17.5 20h-12A1.5 1.5 0 0 1 4 18.5v-12A1.5 1.5 0 0 1 5.5 5H10"></path>
    </svg>
  `;
}

function hypurrscanAddressUrl(address) {
  return `https://hypurrscan.io/address/${String(address || '').toLowerCase()}#more`;
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
function isXyzDexCoin(coin, dex = '') {
  const raw = String(coin || '').trim();
  const upper = raw.toUpperCase();
  const dexUpper = String(dex || '').trim().toUpperCase();

  if (dexUpper === 'XYZ') return true;
  if (upper.startsWith('XYZ:')) return true;
  if (upper.includes(':XYZ:')) return true;
  if (upper.includes('XYZ')) return true;

  return false;
}

function displayCoinLabel(coin) {
  const raw = String(coin || '?').trim();
  if (!raw) return '?';
  const parts = raw.split(':').filter(Boolean);
  return parts.length ? parts[parts.length - 1] : raw;
}

function tokenIconUrl(coin, dex = '') {
  if (isXyzDexCoin(coin, dex)) {
    return '/static/assets/xyz-dex-logo.png';
  }

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
    TRX: 'https://assets.coingecko.com/coins/images/1094/large/tron-logo.png',
    TAO: 'https://assets.coingecko.com/coins/images/28452/large/ARUsPeNQ_400x400.jpeg',
    TON: 'https://assets.coingecko.com/coins/images/17980/large/ton_symbol.png',
    NEAR: 'https://assets.coingecko.com/coins/images/10365/large/near.jpg',
    ADA: 'https://assets.coingecko.com/coins/images/975/large/cardano.png',
    ICP: 'https://assets.coingecko.com/coins/images/14495/large/Internet_Computer_logo.png',
    SEI: 'https://assets.coingecko.com/coins/images/28205/large/Sei_Logo_-_Transparent.png',
    PUMP: 'https://assets.coingecko.com/coins/images/34478/large/pump.png',
    ZEC: 'https://assets.coingecko.com/coins/images/486/large/circle-zcash-color.png',
    MSFT: 'https://assets.coingecko.com/coins/images/0/large/microsoft.png',
  };
  return icons[c] || (c ? `/api/token-icon/${encodeURIComponent(c)}` : '');
}

function coinIconHtml(coin, iconUrl = '', dex = '') {
  const safeCoin = (coin || '?').toString();
  const label = displayCoinLabel(safeCoin);
  const src = iconUrl || tokenIconUrl(safeCoin, dex);
  if (src) {
    return `<img class="coin-img" src="${src}" alt="${label}" loading="lazy" onerror="this.replaceWith(Object.assign(document.createElement('div'), {className: 'coin-icon ' + coinClass('${label}'), textContent: '${label[0] || '?'}'}))">`;
  }
  return `<div class="coin-icon ${coinClass(label)}">${label[0] || '?'}</div>`;
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
  if (!(state.closedVaults instanceof Set)) state.closedVaults = new Set(Array.isArray(state.closedVaults) ? state.closedVaults : []);
}


function singleSlotLimit() {
  return 10;
}

function multiSlotLimit() {
  return state.mainView === 'fatbot-vaults' ? 10 : 10;
}

function unlockedVaultSlotLimit() {
  return 3;
}

function vaultSlotUnlockVolume(slotNumber) {
  return Math.max(1, Number(slotNumber || 1) - unlockedVaultSlotLimit()) * 100000;
}

function vaultSlotUnlockAmountLabel(slotNumber) {
  return `${Math.round(vaultSlotUnlockVolume(slotNumber)).toLocaleString('en-US').replace(/,/g, ' ')} USD`;
}

function vaultSlotUnlockText(slotNumber) {
  return `Reach ${vaultSlotUnlockAmountLabel(slotNumber)} Perps volume to unlock this slot.`;
}

function isCopytradingView() {
  return state.mainView !== 'fatbot-vaults';
}

function isFatBotVaultsView() {
  return state.mainView === 'fatbot-vaults';
}

function isFatBotVaultAddMode() {
  const multiPanel = document.getElementById('multiSectionPanel');
  const multiVisible = !!multiPanel && multiPanel.style.display !== 'none';
  return isFatBotVaultsView() || multiVisible || state.copySetupMode === 'multi' || !!state.activeVaultBuilderSlot;
}



// v123 fixed category runtime helpers.
function categoryMarketType(tab) {
  if (tab === 'tradfi') return 'tradfi';
  if (tab === 'crypto') return 'crypto';
  return 'all';
}

function syncCategoryToMarketFilter() {
  const f = state.leaderboardFilters || {};
  f.window = '30d';
  f.sortBy = 'totalPnl';
  f.minTrades = 0;
  f.minDaysActive = 0;
  f.limit = 50;
  f.marketType = categoryMarketType(state.activeLeaderTab);
  state.leaderboardFilters = f;
}

async function reloadLeaderboardOnly() {
  const list = document.getElementById('traderList');
  if (list) {
    list.classList.add('loading');
    list.innerHTML = 'Loading cached leaderboard...';
  }

  readLeaderboardFiltersFromDom();
  syncCategoryToMarketFilter();
  renderLeaderboardTabs();

  const snapshotCategory = activeSnapshotCategory();
  if (snapshotCategory) {
    try {
      await loadSnapshotCategory(snapshotCategory);
      return;
    } catch (err) {
      console.error('snapshot category load failed', err);
      if (snapshotCategory !== 'trades') {
        if (list) list.innerHTML = `<div class="empty-state">Snapshot load failed:<br><small>${err.message || err}</small></div>`;
        return;
      }
      // Top Trades fallback stays fast and preserves current MVP behavior.
    }
  }

  const q = leaderboardQueryString();

  try {
    const [traders, fatbotVaults] = await Promise.all([
      api(`/api/traders?${q}`),
      api(`/api/fatbot-vaults?${q}`),
    ]);
    state.traders = traders || [];
    state.fatbotVaults = fatbotVaults || [];
    renderLeaderboardTabs();
    renderTraders();
  } catch (err) {
    console.error('category load failed', err);
    if (list) list.innerHTML = `<div class="empty-state">Leaderboard category load failed:<br><small>${err.message || err}</small></div>`;
  }
}

function bindLeaderboardCategoryTabs() {
  document.querySelectorAll('[data-leader-tab]').forEach(btn => {
    btn.addEventListener('click', async () => {
      state.activeLeaderTab = btn.dataset.leaderTab || 'tradfi';
      renderLeaderboardTabs();
      await reloadLeaderboardOnly();
    });
  });
}


function leaderboardQueryString() {
  const f = state.leaderboardFilters || {};
  // Leaderboard displayed metrics are intentionally fixed to 30D.
  const params = new URLSearchParams({
    window: '30d',
    sortBy: 'totalPnl',
    minTrades: String(f.minTrades ?? 0),
    minDaysActive: String(f.minDaysActive ?? 0),
    limit: String(f.limit ?? 50),
    marketType: f.marketType || 'all',
  });
  return params.toString();
}


function activeSnapshotCategory() {
  const tab = String(state.activeLeaderTab || 'trades');
  if (['trades', 'tradfi', 'crypto', 'bull', 'bear', 'fatbot_selection'].includes(tab)) return tab;
  return null;
}

function snapshotAgeLabel(ageSeconds) {
  const age = Number(ageSeconds);
  if (!Number.isFinite(age)) return '';
  if (age < 60) return `updated ${Math.max(1, Math.round(age))}s ago`;
  return `updated ${Math.round(age / 60)}m ago`;
}

function renderSnapshotStatus(snapshot) {
  state.leaderboardSnapshotStatus = snapshot || null;
  const hint = $('leaderboardHint');
  if (!hint || !snapshot || !snapshot.category) return;

  const age = snapshotAgeLabel(snapshot.age_seconds);
  const status = snapshot.status === 'ready' ? (age ? ` · ${age}` : '') : ` · ${snapshot.status || 'preparing'}`;
  hint.textContent = `${hint.textContent}${status}`;
}

async function loadSnapshotCategory(category) {
  const snapshot = await api(`/api/leaderboard-snapshot/${category}`);
  renderSnapshotStatus(snapshot);

  if (Array.isArray(snapshot.rows) && snapshot.rows.length) {
    state.traders = snapshot.rows;
    renderLeaderboardTabs();
    renderSnapshotStatus(snapshot);
    renderTraders();
    return true;
  }

  const list = document.getElementById('traderList');
  if (list) {
    const err = snapshot.error ? `<br><small>${snapshot.error}</small>` : '';
    list.classList.remove('loading');
    list.innerHTML = `<div class="empty-state">Preparing ${category} leaderboard snapshot...<br><small>Server is precomputing this category in the background. Refresh shortly.</small>${err}</div>`;
  }
  return false;
}


function readLeaderboardFiltersFromDom() {
  // v122: free filter UI removed. Categories are fixed.
  state.leaderboardFilters = {
    window: '30d',
    sortBy: 'totalPnl',
    minTrades: 0,
    minDaysActive: 0,
    limit: 50,
    marketType: categoryMarketType(state.activeLeaderTab),
  };
}


function bindLeaderboardFilters() {
  // v122: no free filter controls. Leaderboard reloads only through fixed categories.
}



function apiWithTimeout(path, timeoutMs = 12000) {
  return Promise.race([
    api(path),
    new Promise((_, reject) => setTimeout(() => reject(new Error(`Request timeout after ${Math.round(timeoutMs / 1000)}s`)), timeoutMs)),
  ]);
}

async function loadAll() {
  ensureUiState();
  syncCategoryToMarketFilter();
  renderTopInfoPanel();
  const q = leaderboardQueryString();
  const errors = [];

  const safe = (key, promise, onData) => {
    promise
      .then(data => {
        onData(data);
      })
      .catch(err => {
        console.error(`${key} load failed`, err);
        errors.push(`${key}: ${err.message || err}`);
        const list = document.getElementById('traderList');
        if (key === 'traders' && list && !(state.traders || []).length) {
          list.innerHTML = `<div class="empty-state">Top Traders failed to load.<br><small>${err.message || err}</small></div>`;
        }
      });
  };

  // Render each section immediately when its endpoint finishes instead of waiting
  // for all endpoints. Functionality is the same, perceived loading is much faster.
  safe('summary', api('/api/summary'), data => renderSummary(data));

  safe('wallets', api('/api/wallets'), data => {
    state.wallets = data || [];
    renderCopySections(state.wallets);
    renderMultiLeaderboard(state.pools || [], state.wallets);
  });

  safe('livePositions', api('/api/live-positions'), data => {
    state.livePositions = data || [];
    renderLiveTraderFeed(state.livePositions);
  });

  safe('pools', api('/api/pools'), data => {
    state.pools = data || [];
    renderMultiLeaderboard(state.pools, state.wallets || []);
  });

  const snapshotCategory = activeSnapshotCategory();
  if (snapshotCategory) {
    safe('leaderboardSnapshot', api(`/api/leaderboard-snapshot/${snapshotCategory}`), snapshot => {
      renderSnapshotStatus(snapshot);
      if (Array.isArray(snapshot.rows) && snapshot.rows.length) {
        state.traders = snapshot.rows;
        renderLeaderboardTabs();
        renderSnapshotStatus(snapshot);
        renderTraders();
      } else {
        const list = document.getElementById('traderList');
        if (list) {
          list.classList.remove('loading');
          list.innerHTML = `<div class="empty-state">Preparing ${snapshotCategory} leaderboard snapshot...<br><small>Server is precomputing this category in the background.</small></div>`;
        }
      }
    });
  } else {
    safe('traders', api(`/api/traders?${q}`), data => {
      state.traders = data || [];
      renderLeaderboardTabs();
      renderTraders();
    });
  }

  // Vaults are only needed for Favourite/FatBot Selection and are loaded separately.
  safe('fatbotVaults', api(`/api/fatbot-vaults?${q}`), data => {
    state.fatbotVaults = data || [];
    renderLeaderboardTabs();
    renderTraders();
    renderCopySections(state.wallets || []);
    if (state.activeSingleCopyWallet && state.activeSingleCopyWallet.is_model_single_copy) {
      state.activeSingleCopyWallet = modelSingleCopyWallet();
      renderSingleCopyModalContent();
    }
  });
}


function allocationPanelHtml() {
  return `
    <div class="panel-head small">
      <h2>PnL Allocation</h2>
      <span class="pill">DEMO</span>
    </div>
    <div class="donut-wrap">
      <div class="donut"><span id="allocPct">48%</span></div>
      <div class="legend">
        <div><i class="dot purple"></i><span>Single Trader Copy</span><strong id="allocSingle">$0.00</strong></div>
        <div><i class="dot yellow"></i><span>Multi Copy</span><strong id="allocPool">$0.00</strong></div>
        <div><i class="dot green"></i><span>Available</span><strong id="allocAvailable">$0.00</strong></div>
      </div>
    </div>
  `;
}

function fatbotHowItWorksHtml() {
  const index = Number(state.howItWorksIndex || 0) % FATBOT_HOW_IT_WORKS_STEPS.length;
  const stepText = FATBOT_HOW_IT_WORKS_STEPS[index];
  const dots = FATBOT_HOW_IT_WORKS_STEPS.map((_, i) => `<i class="how-it-works-dot ${i === index ? 'active' : ''}"></i>`).join('');
  return `
    <div class="panel-head small">
      <h2>How it Works</h2>
      <span class="pill">AUTO LOOP</span>
    </div>
    <div class="how-it-works-wrap">
      <div class="how-it-works-line" aria-live="polite">
        <span class="how-it-works-step">${index + 1}</span>
        <span class="how-it-works-text">${stepText}</span>
      </div>
      <div class="how-it-works-dots">${dots}</div>
    </div>
  `;
}

function renderTopInfoPanel() {
  const panel = document.getElementById('topInfoPanel');
  if (!panel) return;
  panel.innerHTML = state.mainView === 'fatbot-vaults' ? fatbotHowItWorksHtml() : allocationPanelHtml();
}

function ensureFatbotHowItWorksLoop() {
  if (fatbotHowItWorksTimer) return;
  fatbotHowItWorksTimer = setInterval(() => {
    state.howItWorksIndex = (Number(state.howItWorksIndex || 0) + 1) % FATBOT_HOW_IT_WORKS_STEPS.length;
    if (state.mainView === 'fatbot-vaults') renderTopInfoPanel();
  }, 3000);
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
  if (state.mainView !== 'fatbot-vaults') renderTopInfoPanel();
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
  const top = Array.isArray(state.traders) ? state.traders : [];
  const vaults = Array.isArray(state.fatbotVaults) ? state.fatbotVaults : [];
  const all = [...top, ...vaults];

  if (state.activeLeaderTab === 'trades') {
    return [...top].sort(pnlSortDesc);
  }

  if (state.activeLeaderTab === 'tradfi') {
    return [...top].sort(pnlSortDesc);
  }

  if (state.activeLeaderTab === 'crypto') {
    return [...top].sort(pnlSortDesc);
  }

  if (state.activeLeaderTab === 'bull') {
    return top
      .filter(t => rowLongShare(t) > 80)
      .sort(pnlSortDesc);
  }

  if (state.activeLeaderTab === 'bear') {
    return top
      .filter(t => rowShortShare(t) > 80)
      .sort(pnlSortDesc);
  }

  if (state.activeLeaderTab === 'fatbot_selection') {
    const selected = normalizedSelectionSet();
    if (!selected.size) return [];
    return all
      .filter(t => selected.has(String(t.address || '').toLowerCase()) || selected.has(String(t.vault_id || '').toLowerCase()))
      .filter(rowHasOpenPositions)
      .sort(pnlSortDesc);
  }

  if (state.activeLeaderTab === 'favourite') {
    return all.filter(t => state.favourites.has(t.vault_id || t.address)).sort(pnlSortDesc);
  }

  return [...top].sort(pnlSortDesc);
}


function renderLeaderboardTabs() {
  document.querySelectorAll('[data-leader-tab]').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.leaderTab === state.activeLeaderTab);
  });

  const fatbotEyebrow = $('fatbotSelectionEyebrow');
  if (fatbotEyebrow) {
    fatbotEyebrow.style.display = state.activeLeaderTab === 'fatbot_selection' ? 'inline-flex' : 'none';
  }

  const hint = $('leaderboardHint');
  if (!hint) return;

  if (state.activeLeaderTab === 'trades') {
    hint.textContent = 'Top Trades: no TradFi/Crypto/Bull/Bear filter. Fixed 30D PnL ranking.';
  } else if (state.activeLeaderTab === 'tradfi') {
    hint.textContent = 'Top TradFi traders: TradFi open-position share ≥ 70%, sorted by 30D PnL.';
  } else if (state.activeLeaderTab === 'crypto') {
    hint.textContent = 'Top Crypto traders: Crypto exposure ≥ 70%, sorted by 30D PnL.';
  } else if (state.activeLeaderTab === 'bull') {
    hint.textContent = 'Top Bull traders: long exposure share > 80%, sorted by 30D PnL.';
  } else if (state.activeLeaderTab === 'bear') {
    hint.textContent = 'Top Bears: short exposure share > 80%, sorted by 30D PnL.';
  } else if (state.activeLeaderTab === 'fatbot_selection') {
    hint.textContent = 'Top FatBot Selection: public Hyperliquid scan of manual wallets, only wallets with open positions, sorted by 30D PnL.';
  } else if (state.activeLeaderTab === 'favourite') {
    hint.textContent = 'Favourite traders and vaults saved locally in this browser.';
  } else {
    hint.textContent = 'Fixed leaderboard category.';
  }
}


function pnlSparklineHtml(t) {
  const values = Array.isArray(t?.pnl_sparkline) ? t.pnl_sparkline.map(Number).filter(Number.isFinite) : [];
  if (values.length < 2) {
    return `<div class="sparkline-empty">—</div>`;
  }

  const width = 132;
  const height = 34;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = Math.max(max - min, 1e-9);

  const points = values.map((value, index) => {
    const x = values.length === 1 ? 0 : (index / (values.length - 1)) * width;
    const y = height - ((value - min) / range) * height;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');

  const endValue = values[values.length - 1] - values[0];
  const cls = endValue >= 0 ? 'positive' : 'negative';
  const label = t.pnl_sparkline_window ? `${String(t.pnl_sparkline_window).toUpperCase()} PnL` : '30D PnL';

  return `
    <div class="sparkline-wrap ${cls}" title="${label}">
      <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-hidden="true">
        <polyline points="${points}" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"></polyline>
      </svg>
    </div>
  `;
}


function renderTraders() {
  const traders = filteredTraders();
  const el = safeClassRemove('traderList', 'loading');
  if (!el) return;

  if (!traders.length) {
    const msg = state.activeLeaderTab === 'favourite'
      ? 'No favourites yet. Click the star on a trader or vault.'
      : state.activeLeaderTab === 'bull'
        ? 'No Top Bull wallets found. Requires long exposure share > 80%.'
        : state.activeLeaderTab === 'bear'
          ? 'No Top Bears wallets found. Requires short exposure share > 80%.'
          : state.activeLeaderTab === 'fatbot_selection'
            ? 'Top FatBot Selection is empty. Manual wallets with no live open positions are hidden by default.'
            : 'No traders available.';
    const f = state.leaderboardFilters || {};
    const marketMsg = f.marketType && f.marketType !== 'all'
      ? `<br><small>Market type uses current open positions from Hyperliquid. Wallets with no current positions are excluded.</small>`
      : '';
    el.innerHTML = `<div class="empty-state">${msg}${marketMsg}</div>`;
    return;
  }

  el.innerHTML = traders.map((t, i) => {
    const favKey = t.vault_id || t.address;
    const isFav = state.favourites.has(favKey);
    const isVault = t.source === 'fatbot_vault';
    const isLive = isHydro(t) || isVault;
    const subtitle = t.source === 'fatbot_selection' ? 'FatBot Selection wallet' : (isVault ? 'FatBot multi-copy vault' : (isLive ? 'Hydromancer 30D PnL leaderboard' : t.label));
    const actionLabel = isFatBotVaultAddMode() && !isVault ? 'Add to vault' : (isVault ? 'Copy Vault' : 'Copy Wallet');
    const displayName = walletDisplayName(t);

    return `
      <div class="trader-row hydro-trader-row ${isVault ? 'fatbot-vault-row' : ''} ${t.fatbot_selection_last_good_retained ? 'last-good-row' : ''}" data-address="${t.address}" data-vault-id="${t.vault_id || ''}">
        <button class="fav-btn ${isFav ? 'active' : ''}" data-fav="${favKey}" title="Favourite">${isFav ? '★' : '☆'}</button>
        ${leaderLogoHtml(t, i)}
        <div>
          <div class="row-title wallet-title-line">
            <span class="wallet-display-name">${displayName}</span>
            <button class="wallet-icon-btn" data-rename-wallet="${t.address}" title="Rename wallet">✎</button>
            <a class="wallet-icon-btn wallet-link-btn" data-wallet-link="1" href="${hypurrscanAddressUrl(t.address)}" target="_blank" rel="noopener noreferrer" title="Open on Hypurrscan">${externalLinkIconSvg()}</a>
          </div>
          <div class="row-sub">${subtitle}</div>
        </div>
        <div>
          <div class="row-sub">30D PnL</div>
          <strong class="${positiveClass(pnlNumber(t))}">${pnlDisplay(t)}</strong>
        </div>
        <div class="optional-leader-col">
          <div class="row-sub">Value</div>
          <strong>${moneyOrDash(t.account_value)}</strong>
        </div>
        <div class="optional-leader-col">
          <div class="row-sub">30D Volume</div>
          <strong>${moneyOrDash(t.volume || t.volume_traded || t.volumeTraded)}</strong>
        </div>
        <div class="optional-leader-col">
          <div class="row-sub">Exposure</div>
          <strong>${grossExposureDisplay(t)}</strong>
        </div>
        <div class="optional-leader-col">
          <div class="row-sub">30D Win Rate</div>
          <strong>${isLive ? winRateDisplay(t) : '—'}</strong>
        </div>
        <div class="sparkline-col">
          <div class="row-sub">PnL Chart</div>
          ${pnlSparklineHtml(t)}
        </div>
        <button class="copy-btn" data-copy="${t.address}" data-vault-copy="${isVault ? '1' : ''}">${actionLabel}</button>
      </div>
    `;
  }).join('');

  el.querySelectorAll('.trader-row').forEach(row => {
    row.addEventListener('click', (e) => {
      if (e.target.closest('[data-copy], [data-fav], [data-rename-wallet], [data-wallet-link]')) return;
      openTrader(row.dataset.address);
    });
  });
  el.querySelectorAll('[data-rename-wallet]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      renameWalletAlias(btn.dataset.renameWallet);
    });
  });
  el.querySelectorAll('[data-wallet-link]').forEach(link => {
    link.addEventListener('click', (e) => e.stopPropagation());
  });
  el.querySelectorAll('[data-copy]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (isFatBotVaultAddMode() && btn.dataset.vaultCopy !== '1') {
        addTraderToVaultBuilder(btn.dataset.copy);
      } else {
        openCopyWizard(btn.dataset.copy);
      }
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


const DEFAULT_FATBOT_VAULT_ADDRESS = '0x0baFb25EF191bFe7A2727E14F5BbfC36610EC62A';
const FATBOT_HOW_IT_WORKS_STEPS = [
  'Create your own vault — safe and profitable',
  'Choose up to 10 top traders you want to copy',
  'Vault will create their average position',
  'Set safety parameters',
  'Launch vault — fully automatic & diversified',
];
let fatbotHowItWorksTimer = null;

function saveDefaultVaultMembers() {
  localStorage.setItem('fatbot_default_vault_members', JSON.stringify(state.defaultVaultMembers || []));
}

function defaultVaultSourceRow() {
  const target = DEFAULT_FATBOT_VAULT_ADDRESS.toLowerCase();
  const live =
    (state.fatbotVaults || []).find(v => String(v.address || '').toLowerCase() === target) ||
    (state.traders || []).find(v => String(v.address || '').toLowerCase() === target) ||
    {};
  return live;
}

function defaultVaultWallet() {
  const live = defaultVaultSourceRow();
  const value = Number(live.account_value || live.value || 0);
  const pnl = Number(live.total_pnl || live.pnl_usd || live.pnl || 0);
  return {
    id: 'default-fatbot-vault',
    wallet_address: DEFAULT_FATBOT_VAULT_ADDRESS,
    address: DEFAULT_FATBOT_VAULT_ADDRESS,
    label: 'My FatBot Vault',
    mode: 'pool',
    status: 'active',
    is_default_vault: true,
    source: 'fatbot_vault',
    value,
    available: Number(live.available || 0),
    total_pnl: pnl,
    realized_pnl: Number(live.realized_pnl || 0),
    unrealized_pnl: Number(live.unrealized_pnl || 0),
    gross_exposure: Number(live.gross_exposure || 0),
    net_exposure: Number(live.net_exposure || 0),
    drift: Number(live.drift || 0),
    positions: Array.isArray(live.positions) ? live.positions : [],
    portfolio_chart_points: live.portfolio_chart_points || [],
    portfolio_chart_window: live.portfolio_chart_window || '30d',
    pnl_sparkline: live.pnl_sparkline || [],
    raw_live_row: live,
  };
}

function vaultManagementPreviewRow(address) {
  const key = String(address || '').toLowerCase();
  return (
    (state.traders || []).find(t => String(t.address || '').toLowerCase() === key) ||
    (state.fatbotVaults || []).find(t => String(t.address || '').toLowerCase() === key) ||
    { address, label: shortAddress(address), source: 'manual_vault_member' }
  );
}


function ensureDefaultVaultPlaceholderMembers() {
  if (!Array.isArray(state.defaultVaultMembers)) state.defaultVaultMembers = [];
  if (state.defaultVaultMembers.length) return;

  const seen = new Set();
  const picked = [];
  (state.traders || []).forEach(t => {
    const addr = String(t.address || '').trim();
    const key = addr.toLowerCase();
    if (isValidWallet(addr) && !seen.has(key) && key !== DEFAULT_FATBOT_VAULT_ADDRESS.toLowerCase() && picked.length < 7) {
      seen.add(key);
      picked.push(addr);
    }
  });

  if (!picked.length) {
    [
      '0xf66f7dba8d4837586078f4fdcdc29804337ca06',
      '0x32008fcf66bbd10532afc83ca8b6c920dae22c407',
      '0xb83de012dba672c76a7dbbbf3e459cb59d7d6e36',
      '0x17c3c80a86654ab6f48c7e17f8d7b8d2e84a8686',
      '0x57ae9ad8212ce7edfdc1e5adcb9cf8d0a8405fd2',
      '0x2808fc407e0a702870378e8990bd005bd3b89fac',
      '0x8bafa7f004264f93e9bc43247786183f6a7fa05'
    ].forEach(addr => picked.push(addr));
  }

  state.defaultVaultMembers = picked.slice(0, 7);
  saveDefaultVaultMembers();
}



function saveVaultMemberOverrides() {
  localStorage.setItem('fatbot_vault_member_overrides', JSON.stringify(state.vaultMemberOverrides || {}));
}

function saveClosedVaults() {
  ensureUiState();
  localStorage.setItem('fatbot_closed_vaults', JSON.stringify([...(state.closedVaults || new Set())]));
}

function closedVaultKey(wallet) {
  if (!wallet) return '';
  if (wallet.is_default_vault) return 'default-fatbot-vault';
  return String(wallet.id || wallet.wallet_address || wallet.address || wallet.label || '').toLowerCase();
}

function isVaultClosed(wallet) {
  ensureUiState();
  return state.closedVaults.has(closedVaultKey(wallet));
}

function isRemovedPresetVault(wallet) {
  // v167: never hide by label.
  // New user-created vaults can legitimately be named FatBot Vault #2 / #3.
  return false;
}

function activeVaultModalWallet() {
  return _activeVaultModalWallet || defaultVaultWallet();
}

function vaultMembersStorageKey(wallet) {
  const raw = wallet?.is_default_vault
    ? `default:${DEFAULT_FATBOT_VAULT_ADDRESS}`
    : (wallet?.wallet_address || wallet?.address || wallet?.id || wallet?.label || 'vault');
  return String(raw).toLowerCase();
}

function genericVaultPlaceholderMembers(limit = 7) {
  const seen = new Set();
  const picked = [];
  (state.traders || []).forEach(t => {
    const addr = String(t.address || '').trim();
    const key = addr.toLowerCase();
    if (isValidWallet(addr) && !seen.has(key) && key !== DEFAULT_FATBOT_VAULT_ADDRESS.toLowerCase() && picked.length < limit) {
      seen.add(key);
      picked.push(addr);
    }
  });
  return picked;
}

function poolForWallet(wallet) {
  const poolId = Number(wallet?.pool_id || 0);
  return (state.pools || []).find(p => Number(p.id || 0) === poolId) || null;
}

function getVaultModalMembers(wallet) {
  const target = wallet || activeVaultModalWallet();
  if (!target) return [];

  const key = vaultMembersStorageKey(target);
  const overrides = state.vaultMemberOverrides || {};
  if (Array.isArray(overrides[key]) && overrides[key].length) {
    return overrides[key].slice(0, 10);
  }

  if (target.is_default_vault) {
    ensureDefaultVaultPlaceholderMembers();
    return (state.defaultVaultMembers || []).slice(0, 10);
  }

  const pool = poolForWallet(target);
  const memberAddresses = Array.isArray(pool?.members)
    ? pool.members.map(m => String(m.trader_address || '').trim()).filter(Boolean)
    : [];
  const unique = [];
  const seen = new Set();
  memberAddresses.forEach(addr => {
    const key = addr.toLowerCase();
    if (isValidWallet(addr) && !seen.has(key)) {
      seen.add(key);
      unique.push(addr);
    }
  });
  if (unique.length) return unique.slice(0, 10);

  return genericVaultPlaceholderMembers(7).slice(0, 10);
}

function setVaultModalMembers(wallet, members) {
  const target = wallet || activeVaultModalWallet();
  if (!target) return;

  const cleaned = [];
  const seen = new Set();
  (Array.isArray(members) ? members : []).forEach(addr => {
    const value = String(addr || '').trim();
    const key = value.toLowerCase();
    if (isValidWallet(value) && !seen.has(key) && cleaned.length < 10) {
      seen.add(key);
      cleaned.push(value);
    }
  });

  if (target.is_default_vault) {
    state.defaultVaultMembers = cleaned;
    saveDefaultVaultMembers();
  }

  const key = vaultMembersStorageKey(target);
  if (!state.vaultMemberOverrides) state.vaultMemberOverrides = {};
  state.vaultMemberOverrides[key] = cleaned;
  saveVaultMemberOverrides();
}

function vaultSourceLookup(address) {
  const key = String(address || '').toLowerCase();
  if (!key || !key.startsWith('0x')) return null;
  return (
    (state.fatbotVaults || []).find(v => String(v.address || '').toLowerCase() === key) ||
    (state.traders || []).find(v => String(v.address || '').toLowerCase() === key) ||
    null
  );
}

function fallbackWalletSparkline(wallet, points = 16) {
  const key = String(wallet?.wallet_address || wallet?.address || wallet?.label || wallet?.id || 'vault');
  let hash = 0;
  for (let i = 0; i < key.length; i += 1) hash = ((hash << 5) - hash) + key.charCodeAt(i);
  const amplitude = Math.max(Math.abs(Number(wallet?.total_pnl || 0)) * 0.08, Math.abs(Number(wallet?.value || 0)) * 0.015, 18);
  const start = Number(wallet?.total_pnl || 0) - amplitude * 0.6;
  const out = [];
  for (let i = 0; i < points; i += 1) {
    const wave = Math.sin((i / Math.max(points - 1, 1)) * Math.PI * 1.9 + (Math.abs(hash) % 13) / 6) * amplitude * 0.35;
    const drift = (i / Math.max(points - 1, 1)) * amplitude * 0.55;
    const noise = (((hash >> (i % 8)) & 7) - 3) * amplitude * 0.03;
    out.push(Number((start + wave + drift + noise).toFixed(2)));
  }
  return out;
}

function resolveVaultWalletSparkline(wallet, preferredWindow = '7d') {
  const target = wallet || activeVaultModalWallet() || {};
  if (Array.isArray(target.pnl_sparkline) && target.pnl_sparkline.length > 1) {
    return {
      values: target.pnl_sparkline.map(Number).filter(Number.isFinite),
      window: target.pnl_sparkline_window || preferredWindow,
      source: 'wallet_row',
    };
  }

  if (target.is_default_vault) {
    const live = defaultVaultSourceRow();
    if (Array.isArray(live?.pnl_sparkline) && live.pnl_sparkline.length > 1) {
      return {
        values: live.pnl_sparkline.map(Number).filter(Number.isFinite),
        window: live.pnl_sparkline_window || preferredWindow,
        source: 'default_vault_live_row',
      };
    }
  }

  const sourceCandidates = [
    vaultSourceLookup(target.wallet_address || target.address),
    vaultSourceLookup(target.copied_trader_address),
  ];
  const pool = poolForWallet(target);
  (pool?.members || []).forEach(member => {
    const row = vaultSourceLookup(member.trader_address);
    if (row) sourceCandidates.push(row);
  });

  const source = sourceCandidates.find(item => Array.isArray(item?.pnl_sparkline) && item.pnl_sparkline.length > 1);
  if (source) {
    return {
      values: source.pnl_sparkline.map(Number).filter(Number.isFinite),
      window: source.pnl_sparkline_window || preferredWindow,
      source: source.source || 'source_row',
    };
  }

  return {
    values: fallbackWalletSparkline(target),
    window: preferredWindow,
    source: 'frontend_fallback_wallet_sparkline',
  };
}

function sparklinePointsToPortfolio(values, accountValue = 0) {
  const safeAccountValue = Math.max(Number(accountValue || 0), 1);
  return values.map((value, idx) => ({
    ts: idx,
    pnl_usd: Number(value),
    account_value: safeAccountValue,
    pnl_equity_pct: (Number(value) / safeAccountValue) * 100,
  }));
}

function walletAgeDays(activatedAt) {
  if (!activatedAt) return 0;
  const ts = new Date(activatedAt).getTime();
  if (!Number.isFinite(ts)) return 0;
  return Math.max(0, Math.floor((Date.now() - ts) / 86400000));
}

function buildVaultModalProfile(wallet) {
  const target = wallet || activeVaultModalWallet() || {};
  const live = target.is_default_vault ? defaultVaultSourceRow() : {};
  const pool = poolForWallet(target);
  const spark = resolveVaultWalletSparkline(target, '7d');
  const positions = Array.isArray(target.positions) && target.positions.length
    ? target.positions
    : (Array.isArray(live?.positions) ? live.positions : []);

  let longNotional = 0;
  let shortNotional = 0;
  let positivePnLCount = 0;
  positions.forEach(p => {
    const notional = Math.abs(Number(p.actual_notional || p.target_notional || p.notional || 0));
    if (String(p.side || '').toLowerCase().includes('short')) shortNotional += notional;
    else longNotional += notional;
    if (Number(p.pnl || 0) > 0) positivePnLCount += 1;
  });
  const totalNotional = longNotional + shortNotional;
  const longPct = totalNotional ? (longNotional / totalNotional) * 100 : Number(live?.long_exposure_share_pct || 0);
  const shortPct = totalNotional ? (shortNotional / totalNotional) * 100 : Number(live?.short_exposure_share_pct || 0);
  const volumeFromPositions = positions.reduce((sum, p) => sum + Math.abs(Number(p.actual_notional || p.target_notional || 0)), 0);

  const merged = {
    ...live,
    ...target,
    address: target.address || target.wallet_address || live?.address || DEFAULT_FATBOT_VAULT_ADDRESS,
    wallet_address: target.wallet_address || target.address || live?.address || DEFAULT_FATBOT_VAULT_ADDRESS,
    label: target.label || live?.label || 'FatBot Vault',
    source: 'fatbot_vault',
    account_value: Number(target.value ?? target.account_value ?? live?.account_value ?? live?.value ?? 0),
    available: Number(target.available ?? live?.available ?? 0),
    total_pnl: Number(target.total_pnl ?? live?.total_pnl ?? live?.pnl_30d ?? live?.pnl_usd ?? 0),
    realized_pnl: Number(target.realized_pnl ?? live?.realized_pnl ?? 0),
    unrealized_pnl: Number(target.unrealized_pnl ?? live?.unrealized_pnl ?? 0),
    gross_exposure: Number(target.gross_exposure ?? live?.gross_exposure ?? 0),
    long_exposure_share_pct: longPct,
    short_exposure_share_pct: shortPct,
    win_rate: Number(live?.win_rate ?? target.win_rate ?? (positions.length ? (positivePnLCount / positions.length) * 100 : 0)),
    total_trades: Number(live?.total_trades ?? target.total_trades ?? positions.length),
    volume: Number(live?.volume ?? target.volume ?? volumeFromPositions),
    account_age_days: Number(live?.account_age_days ?? target.account_age_days ?? walletAgeDays(target.activated_at)),
    open_positions: positions.length,
    positions,
    pool_member_count: Array.isArray(pool?.members) ? pool.members.length : 0,
    pnl_sparkline: spark.values,
    pnl_sparkline_window: spark.window,
    portfolio_chart_points: (Array.isArray(live?.portfolio_chart_points) && live.portfolio_chart_points.length)
      ? live.portfolio_chart_points
      : sparklinePointsToPortfolio(spark.values, Number(target.value ?? target.account_value ?? live?.account_value ?? 0)),
    portfolio_chart_window: (Array.isArray(live?.portfolio_chart_points) && live.portfolio_chart_points.length)
      ? (live.portfolio_chart_window || spark.window || '30d')
      : (spark.window || '7d'),
    portfolio_chart_source: live?.portfolio_chart_source || spark.source,
    vault_modal_source: spark.source,
  };
  return merged;
}

function vaultMiniChartHtml(wallet) {
  const spark = resolveVaultWalletSparkline(wallet, '7d');
  return pnlSparklineHtml({ pnl_sparkline: spark.values, pnl_sparkline_window: spark.window || '7d' });
}

function defaultVaultManagementHtml() {
  const wallet = activeVaultModalWallet();
  const members = getVaultModalMembers(wallet);

  const rows = members.length ? members.map((address, idx) => {
    const t = vaultManagementPreviewRow(address);
    return `
      <div class="vault-management-row">
        ${leaderLogoHtml(t, idx)}
        <div class="vault-management-main">
          <div class="row-title wallet-title-line">
            <span class="wallet-display-name">${walletDisplayName(t)}</span>
            <a class="wallet-icon-btn wallet-link-btn" data-wallet-link="1" href="${hypurrscanAddressUrl(address)}" target="_blank" rel="noopener noreferrer" title="Open on Hypurrscan">${externalLinkIconSvg()}</a>
          </div>
          <div class="row-sub">${shortAddress(address)}</div>
        </div>
        <div><div class="row-sub">30D PnL</div><strong class="${positiveClass(pnlNumber(t))}">${pnlDisplay(t)}</strong></div>
        <div><div class="row-sub">Value</div><strong>${moneyOrDash(t.account_value)}</strong></div>
        <div><div class="row-sub">Exposure</div><strong>${grossExposureDisplay(t)}</strong></div>
        <div class="vault-management-chart">
          <div class="row-sub">30D Chart</div>
          ${pnlSparklineHtml(t)}
        </div>
        <button class="vault-trash-btn" type="button" data-remove-default-vault-member="${idx}" title="Remove trader">🗑</button>
      </div>
    `;
  }).join('') : `
    <div class="empty-state compact-empty">No wallet members saved yet. Add wallets from leaderboard or paste a manual address below.</div>
  `;

  return `
    <div class="vault-management-panel">
      <div class="vault-management-list">${rows}</div>
      <div class="vault-management-add">
        <input id="defaultVaultAddInput" class="form-input" placeholder="Paste wallet address 0x..." />
        <button class="secondary" type="button" id="defaultVaultAddBtn">Add wallet</button>
      </div>
      <div class="vault-management-actions">
        <button class="danger-outline-btn" type="button" id="defaultVaultCloseBtn">Close Vault</button>
        <button class="primary" type="button" id="defaultVaultSaveBtn">Save settings</button>
      </div>
      ${closeVaultDialogHtml()}
    </div>
  `;
}


function closeVaultDialogHtml() {
  if (!state.closeVaultDialogOpen) return '';
  const wallet = activeVaultModalWallet();
  const label = wallet?.label || 'FatBot Vault';
  return `
    <div class="vault-close-dialog-backdrop" data-close-vault-dialog-backdrop="1">
      <div class="vault-close-dialog" role="dialog" aria-modal="true" aria-label="Close Vault">
        <div class="vault-close-dialog-head">
          <div>
            <span class="pill danger-pill">CLOSE VAULT</span>
            <h3>Close ${label}</h3>
            <p class="muted">Insert wallet address where funds should be withdrawn. Then confirm vault close.</p>
          </div>
          <button class="wallet-icon-btn" type="button" data-close-vault-dialog-cancel="1">×</button>
        </div>
        <label class="form-label">Withdraw funds to wallet</label>
        <input id="closeVaultWithdrawInput" class="form-input" placeholder="Destination wallet 0x..." value="${state.closeVaultWithdrawAddress || ''}" />
        <div class="vault-close-warning ${state.closeVaultConfirmArmed ? 'armed' : ''}">
          ${state.closeVaultConfirmArmed
            ? 'Final confirmation required. Click Confirm Close Vault to close this vault and remove it from My Vaults.'
            : 'This will remove the vault from your My Vaults portfolio and leave the slot empty.'}
        </div>
        <div class="vault-close-actions">
          <button class="secondary" type="button" data-close-vault-dialog-cancel="1">Cancel</button>
          <button class="danger-btn" type="button" id="confirmCloseVaultBtn">${state.closeVaultConfirmArmed ? 'Confirm Close Vault' : 'Close Vault'}</button>
        </div>
      </div>
    </div>
  `;
}

function openCloseVaultDialog() {
  state.closeVaultDialogOpen = true;
  state.closeVaultWithdrawAddress = '';
  state.closeVaultConfirmArmed = false;
  renderDefaultVaultModalContent();
  setTimeout(() => {
    const input = document.getElementById('closeVaultWithdrawInput');
    if (input) input.focus();
  }, 0);
}

function closeCloseVaultDialog() {
  state.closeVaultDialogOpen = false;
  state.closeVaultWithdrawAddress = '';
  state.closeVaultConfirmArmed = false;
  renderDefaultVaultModalContent();
}

function confirmCloseVaultFromDialog() {
  const input = document.getElementById('closeVaultWithdrawInput');
  const value = String(input?.value || '').trim();
  if (!isValidWallet(value)) {
    alert('Enter a valid wallet address starting with 0x.');
    if (input) input.focus();
    return;
  }

  if (!state.closeVaultConfirmArmed) {
    state.closeVaultWithdrawAddress = value;
    state.closeVaultConfirmArmed = true;
    renderDefaultVaultModalContent();
    setTimeout(() => {
      const confirmBtn = document.getElementById('confirmCloseVaultBtn');
      if (confirmBtn) confirmBtn.focus();
    }, 0);
    return;
  }

  const currentVault = activeVaultModalWallet();
  const key = closedVaultKey(currentVault);
  if (key) {
    ensureUiState();
    state.closedVaults.add(key);
    saveClosedVaults();
  }

  if (currentVault && currentVault.id) {
    state.wallets = (state.wallets || []).filter(w => String(w.id) !== String(currentVault.id));
  }

  state.closeVaultDialogOpen = false;
  state.closeVaultWithdrawAddress = '';
  state.closeVaultConfirmArmed = false;
  clearDefaultVaultModalSizing();
  closeModal('traderModal');
  renderCopySections(state.wallets || []);
  renderMultiLeaderboard(state.pools || [], state.wallets || []);
}

function bindCloseVaultDialog() {
  document.querySelectorAll('[data-close-vault-dialog-cancel], [data-close-vault-dialog-backdrop]').forEach(el => {
    el.addEventListener('click', (e) => {
      if (e.target !== el && el.dataset.closeVaultDialogBackdrop) return;
      closeCloseVaultDialog();
    });
  });

  const input = document.getElementById('closeVaultWithdrawInput');
  if (input) {
    input.addEventListener('input', () => {
      state.closeVaultWithdrawAddress = input.value.trim();
      if (state.closeVaultConfirmArmed) {
        state.closeVaultConfirmArmed = false;
        renderDefaultVaultModalContent();
      }
    });
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') confirmCloseVaultFromDialog();
      if (e.key === 'Escape') closeCloseVaultDialog();
    });
  }

  const confirmBtn = document.getElementById('confirmCloseVaultBtn');
  if (confirmBtn) {
    confirmBtn.addEventListener('click', confirmCloseVaultFromDialog);
  }
}


function bindDefaultVaultManagement() {
  const wallet = activeVaultModalWallet();
  document.querySelectorAll('[data-wallet-link]').forEach(link => {
    link.addEventListener('click', (e) => e.stopPropagation());
  });

  document.querySelectorAll('[data-remove-default-vault-member]').forEach(btn => {
    btn.addEventListener('click', () => {
      const idx = Number(btn.dataset.removeDefaultVaultMember || 0);
      const members = getVaultModalMembers(wallet);
      const address = members[idx];
      const ok = confirm(`Remove ${shortAddress(address)} from this vault?`);
      if (!ok) return;
      members.splice(idx, 1);
      setVaultModalMembers(wallet, members);
      renderDefaultVaultModalContent();
    });
  });

  const addBtn = document.getElementById('defaultVaultAddBtn');
  const input = document.getElementById('defaultVaultAddInput');
  if (addBtn && input) {
    addBtn.addEventListener('click', () => {
      const value = input.value.trim();
      if (!isValidWallet(value)) {
        alert('Enter a valid wallet address starting with 0x.');
        return;
      }
      const members = getVaultModalMembers(wallet);
      if (!members.some(x => String(x).toLowerCase() === value.toLowerCase())) {
        members.push(value);
      }
      setVaultModalMembers(wallet, members);
      renderDefaultVaultModalContent();
    });
  }

  const saveBtn = document.getElementById('defaultVaultSaveBtn');
  if (saveBtn) {
    saveBtn.addEventListener('click', () => {
      setVaultModalMembers(wallet, getVaultModalMembers(wallet));
      alert('Vault settings saved.');
    });
  }

  const closeVaultBtn = document.getElementById('defaultVaultCloseBtn');
  if (closeVaultBtn) {
    closeVaultBtn.addEventListener('click', openCloseVaultDialog);
  }

  bindCloseVaultDialog();
}


function livePositionRowHtml(p) {
  const coin = p.coin || p.symbol || '?';
  const side = p.side || '';
  const notional = Number(p.notional || p.target_notional || p.actual_notional || 0);
  const entry = p.entry || p.entry_px || p.entryPrice || p.entry_price;
  const mark = p.mark || p.live_price || p.markPx || p.mid || p.price;
  const pnl = Number(p.pnl || p.unrealized_pnl || 0);
  const liq = p.liq_price || p.liquidation_price || p.liquidationPx || p.liq || '—';
  return `
    <div class="position-row profile-position-row">
      ${coinIconHtml(coin, p.icon_url || tokenIconUrl(coin, p.dex), p.dex)}
      <div><div class="row-title coin-side ${sideClass(side)}">${displayCoinLabel(coin)}</div><div class="row-sub">${side}</div></div>
      <div><div class="row-sub">Notional</div><strong>${fmtUsd(notional)}</strong></div>
      <div><div class="row-sub">Entry</div><strong>${entry || '—'}</strong></div>
      <div><div class="row-sub">Live Price</div><strong>${fmtLivePrice(mark)}</strong></div>
      <div><div class="row-sub">PnL</div><strong class="${positiveClass(pnl)}">${fmtUsd(pnl)}</strong></div>
      <div><div class="row-sub">Liq</div><strong>${fmtLivePrice(liq)}</strong></div>
    </div>
  `;
}

function defaultVaultStatsHtml(vaultProfile) {
  const trader = vaultProfile || defaultVaultSourceRow() || {};
  trader.address = trader.address || DEFAULT_FATBOT_VAULT_ADDRESS;
  trader.source = trader.source || 'fatbot_vault';

  if ((!Array.isArray(trader.portfolio_chart_points) || !trader.portfolio_chart_points.length) && Array.isArray(trader.pnl_sparkline) && trader.pnl_sparkline.length) {
    trader.portfolio_chart_points = trader.pnl_sparkline.map((value, idx) => ({
      ts: idx,
      pnl_usd: Number(value),
      account_value: Number(trader.account_value || 0),
      pnl_equity_pct: Number(trader.account_value || 0) ? Number(value) / Number(trader.account_value || 1) * 100 : 0,
    }));
    trader.portfolio_chart_window = trader.pnl_sparkline_window || '30d';
    trader.portfolio_chart_source = trader.pnl_sparkline_source || 'leaderboard_pnl_sparkline_fallback';
  }

  const positions = Array.isArray(trader.positions) ? trader.positions : [];

  const cards = `
    <div class="vault-stats-grid-3x3">
      <div class="detail-card"><span>PnL Window (30D)</span><strong class="${positiveClass(pnlUsdValue(trader))}">${fmtUsd(pnlUsdValue(trader))}</strong></div>
      <div class="detail-card"><span>Account Value</span><strong>${moneyOrDash(trader.account_value)}</strong></div>
      <div class="detail-card"><span>Long / Short</span><strong>${exposureShareDisplay(trader)}</strong></div>
      <div class="detail-card"><span>Gross Exposure</span><strong>${grossExposureDisplay(trader)}</strong></div>
      <div class="detail-card"><span>30D Win Rate</span><strong>${winRateDisplay(trader)}</strong></div>
      <div class="detail-card"><span>30D Trades</span><strong>${Number(trader.total_trades || trader.trades || 0).toLocaleString()}</strong></div>
      <div class="detail-card"><span>Account Age</span><strong>${Number(trader.account_age_days || 0)} days</strong></div>
      <div class="detail-card"><span>30D Volume</span><strong>${moneyOrDash(trader.volume || trader.volume_traded || trader.volumeTraded)}</strong></div>
      <div class="detail-card"><span>Live Positions</span><strong>${positions.length || Number(trader.open_positions || 0) || 0}</strong></div>
    </div>
  `;

  const posRows = positions.length ? `
    <h3 class="positions-heading">Live Hyperliquid positions</h3>
    <div class="positions-list">
      ${positions.map(p => livePositionRowHtml(p)).join('')}
    </div>
  ` : `<div class="empty-state compact-empty">No live positions returned for this vault yet.</div>`;

  const warning = trader.profile_warning ? `<div class="empty-state compact-empty vault-live-warning">${trader.profile_warning}</div>` : '';
  const chartHtml = profileChartsHtml(trader) || `<div class="profile-chart-section profile-chart-section-top"><div class="profile-chart-single-card"><div class="profile-chart-empty">30D vault chart is loading from Hyperliquid portfolio data...</div></div></div>`;
  return `
    ${warning}
    ${chartHtml}
    ${cards}
    ${posRows}
  `;
}

let _activeDefaultVaultProfile = null;
let _activeVaultModalWallet = null;

async function openDefaultVaultModal(wallet) {
  state.defaultVaultModalTab = 'stats';
  state.closeVaultDialogOpen = false;
  state.closeVaultWithdrawAddress = '';
  state.closeVaultConfirmArmed = false;
  _activeVaultModalWallet = wallet || defaultVaultWallet();
  _activeDefaultVaultProfile = buildVaultModalProfile(_activeVaultModalWallet);
  const el = document.getElementById('traderModalContent');
  const traderModalCard = document.querySelector('#traderModal .modal-card');
  if (traderModalCard) traderModalCard.classList.add('default-vault-modal-card');

  const headerWallet = _activeVaultModalWallet || {};
  const headerAddress = headerWallet.address || headerWallet.wallet_address || DEFAULT_FATBOT_VAULT_ADDRESS;

  el.innerHTML = `
    <button class="profile-back-btn" data-profile-back="1" title="Back">←</button>
    <div class="wizard-head trader-profile-head with-back-button vault-modal-head">
      <div>
        <span class="pill">FATBOT VAULT</span>
        <div style="display:flex; align-items:center; gap:12px; margin-top:10px;">
          ${copyWalletLogoHtml('pool')}
          <div>
            <h2 style="margin:0;">${headerWallet?.label || 'FatBot Vault'}</h2>
            <p class="muted" style="margin:4px 0 0;">${shortAddress(headerAddress)}</p>
          </div>
        </div>
      </div>
      <div class="vault-modal-tabs">
        <button class="vault-modal-tab active" data-default-vault-tab="stats">VAULT STATS</button>
        <button class="vault-modal-tab" data-default-vault-tab="management">WALLET MANAGEMENT</button>
      </div>
    </div>
    <div id="defaultVaultModalBody"></div>
  `;

  el.querySelector('[data-profile-back]').addEventListener('click', () => { clearDefaultVaultModalSizing(); closeModal('traderModal'); });
  bindDefaultVaultTabs();
  openModal('traderModal');
  renderDefaultVaultModalContent();
}

function clearDefaultVaultModalSizing() {
  state.closeVaultDialogOpen = false;
  state.closeVaultWithdrawAddress = '';
  state.closeVaultConfirmArmed = false;
  const traderModalCard = document.querySelector('#traderModal .modal-card');
  if (traderModalCard) traderModalCard.classList.remove('default-vault-modal-card');
}

function bindDefaultVaultTabs() {
  document.querySelectorAll('[data-default-vault-tab]').forEach(btn => {
    btn.addEventListener('click', () => {
      state.defaultVaultModalTab = btn.dataset.defaultVaultTab === 'management' ? 'management' : 'stats';
      renderDefaultVaultModalContent();
    });
  });
}

function renderDefaultVaultModalContent() {
  const body = document.getElementById('defaultVaultModalBody');
  if (!body) return;

  try {
    document.querySelectorAll('[data-default-vault-tab]').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.defaultVaultTab === state.defaultVaultModalTab);
    });

    if (state.defaultVaultModalTab === 'management') {
      body.innerHTML = defaultVaultManagementHtml();
      bindDefaultVaultManagement();
    } else {
      const trader = buildVaultModalProfile(activeVaultModalWallet());
      _activeDefaultVaultProfile = trader;
      body.innerHTML = defaultVaultStatsHtml(trader);
      bindProfileChartToggle(trader);
    }
  } catch (err) {
    console.error('default vault modal render failed', err);
    const trader = _activeDefaultVaultProfile || buildVaultModalProfile(activeVaultModalWallet()) || defaultVaultSourceRow() || {};
    const positions = Array.isArray(trader.positions) ? trader.positions : [];
    body.innerHTML = `
      <div class="empty-state compact-empty vault-live-warning">
        Vault UI fallback rendered because a profile widget failed: ${err.message || err}
      </div>
      <div class="vault-stats-grid-3x3">
        <div class="detail-card"><span>30D PnL</span><strong class="${positiveClass(pnlUsdValue(trader))}">${fmtUsd(pnlUsdValue(trader))}</strong></div>
        <div class="detail-card"><span>Account Value</span><strong>${moneyOrDash(trader.account_value)}</strong></div>
        <div class="detail-card"><span>Long / Short</span><strong>${exposureShareDisplay(trader)}</strong></div>
        <div class="detail-card"><span>Gross Exposure</span><strong>${grossExposureDisplay(trader)}</strong></div>
        <div class="detail-card"><span>30D Win Rate</span><strong>${winRateDisplay(trader)}</strong></div>
        <div class="detail-card"><span>30D Trades</span><strong>${Number(trader.total_trades || trader.trades || 0).toLocaleString()}</strong></div>
        <div class="detail-card"><span>Account Age</span><strong>${Number(trader.account_age_days || 0)} days</strong></div>
        <div class="detail-card"><span>30D Volume</span><strong>${moneyOrDash(trader.volume || trader.volume_traded || trader.volumeTraded)}</strong></div>
        <div class="detail-card"><span>Live Positions</span><strong>${positions.length || Number(trader.open_positions || 0) || 0}</strong></div>
      </div>
    `;
  }
}



function singleCopyPositionsHtml(wallet) {
  const positions = Array.isArray(wallet?.positions) ? wallet.positions : [];
  if (!positions.length) {
    return `<div class="empty-state compact-empty">No open positions yet.</div>`;
  }
  return positions.map(p => `
    <div class="wallet-position-row single-copy-position-row">
      ${coinIconHtml(p.coin, p.icon_url || tokenIconUrl(p.coin, p.dex), p.dex)}
      <div><div class="row-title coin-side ${sideClass(p.side)}">${displayCoinLabel(p.coin)}</div><div class="row-sub">${p.side}</div></div>
      <div><div class="row-sub">Target</div><strong>${fmtUsd(p.target_notional)}</strong></div>
      <div><div class="row-sub">Actual</div><strong>${fmtUsd(p.actual_notional)}</strong></div>
      <div><div class="row-sub">Drift</div><strong class="${positiveClass(p.drift_pct)}">${fmtPct(p.drift_pct)}</strong></div>
      <div><div class="row-sub">PnL</div><strong class="${positiveClass(p.pnl)}">${fmtUsd(p.pnl)}</strong></div>
    </div>
  `).join('');
}

function singleCopyCloseDialogHtml() {
  if (!state.singleCopyCloseDialogOpen) return '';
  const wallet = state.activeSingleCopyWallet || {};
  return `
    <div class="vault-close-dialog-backdrop" data-single-copy-close-backdrop="1">
      <div class="vault-close-dialog single-copy-close-dialog" role="dialog" aria-modal="true" aria-label="Close Copytrading">
        <div class="vault-close-dialog-head">
          <div>
            <span class="pill danger-pill">CLOSE COPYTRADING</span>
            <h3>Close ${wallet.label || 'Copytrading Wallet'}</h3>
            <p class="muted">Insert wallet address where funds should be withdrawn. Then confirm copytrading close.</p>
          </div>
          <button class="wallet-icon-btn" type="button" data-single-copy-close-cancel="1">×</button>
        </div>
        <label class="form-label">Withdraw funds to wallet</label>
        <input id="singleCopyWithdrawInput" class="form-input" placeholder="Destination wallet 0x..." value="${state.singleCopyCloseWithdrawAddress || ''}" />
        <div class="vault-close-warning ${state.singleCopyCloseConfirmArmed ? 'armed' : ''}">
          ${state.singleCopyCloseConfirmArmed
            ? 'Final confirmation required. Click Confirm Close Copytrading to remove this wallet from My Copytrading.'
            : 'This will close this copytrading wallet, withdraw funds, and remove it from your portfolio preview.'}
        </div>
        <div class="vault-close-actions">
          <button class="secondary" type="button" data-single-copy-close-cancel="1">Cancel</button>
          <button class="danger-btn" type="button" id="confirmSingleCopyCloseBtn">${state.singleCopyCloseConfirmArmed ? 'Confirm Close Copytrading' : 'Close Copytrading'}</button>
        </div>
      </div>
    </div>
  `;
}

function renderSingleCopyModalContent() {
  const wallet = state.activeSingleCopyWallet || {};
  const el = document.getElementById('traderModalContent');
  if (!el) return;

  el.innerHTML = `
    <button class="profile-back-btn" data-single-copy-back="1" title="Back">←</button>
    <div class="wizard-head trader-profile-head with-back-button single-copy-modal-head">
      <div>
        <span class="pill">SINGLE COPYTRADING</span>
        <div class="single-copy-header-row">
          ${copyWalletLogoHtml('single')}
          <div>
            <h2>${wallet.label || 'Copytrading Wallet'}</h2>
            <p class="muted">${shortAddress(wallet.wallet_address || '')} · Copying ${shortAddress(wallet.copied_trader_address || '')}${wallet.is_model_single_copy ? ' · model preview data' : ''}</p>
          </div>
        </div>
      </div>
      <button class="danger-outline-btn" type="button" id="openSingleCopyCloseBtn">Close Copytrading</button>
    </div>

    <div class="detail-grid single-copy-detail-grid">
      <div class="detail-card"><span>Wallet value</span><strong>${fmtUsd(wallet.value)}</strong></div>
      <div class="detail-card"><span>Available</span><strong>${fmtUsd(wallet.available)}</strong></div>
      <div class="detail-card"><span>Realized PnL</span><strong class="${positiveClass(wallet.realized_pnl)}">${fmtUsd(wallet.realized_pnl)}</strong></div>
      <div class="detail-card"><span>Unrealized PnL</span><strong class="${positiveClass(wallet.unrealized_pnl)}">${fmtUsd(wallet.unrealized_pnl)}</strong></div>
      <div class="detail-card"><span>Gross Exposure</span><strong>${Number(wallet.gross_exposure || 0).toFixed(2)}x</strong></div>
      <div class="detail-card"><span>Drift</span><strong>${Number(wallet.drift || 0).toFixed(1)}%</strong></div>
    </div>

    <h3 class="positions-heading">Open positions</h3>
    <div class="wallet-position-list single-copy-position-list">
      ${singleCopyPositionsHtml(wallet)}
    </div>

    ${singleCopyCloseDialogHtml()}
  `;

  const backBtn = el.querySelector('[data-single-copy-back]');
  if (backBtn) {
    backBtn.addEventListener('click', () => {
      closeSingleCopyModal();
    });
  }

  const closeBtn = document.getElementById('openSingleCopyCloseBtn');
  if (closeBtn) {
    closeBtn.addEventListener('click', openSingleCopyCloseDialog);
  }

  bindSingleCopyCloseDialog();
}

function openSingleCopyModal(wallet) {
  state.activeSingleCopyWallet = wallet || null;
  state.singleCopyCloseDialogOpen = false;
  state.singleCopyCloseWithdrawAddress = '';
  state.singleCopyCloseConfirmArmed = false;

  const card = document.querySelector('#traderModal .modal-card');
  if (card) {
    card.classList.remove('default-vault-modal-card');
    card.classList.add('single-copy-modal-card');
  }

  renderSingleCopyModalContent();
  openModal('traderModal');

  if (wallet && wallet.is_model_single_copy) {
    apiWithTimeout(`/api/fatbot-vaults?${leaderboardQueryString()}`, 18000)
      .then(rows => {
        const target = MODEL_SINGLE_COPY_ADDRESS.toLowerCase();
        const live = (Array.isArray(rows) ? rows : []).find(v => String(v.address || '').toLowerCase() === target);
        if (live) {
          state.fatbotVaults = [
            live,
            ...(state.fatbotVaults || []).filter(v => String(v.address || '').toLowerCase() !== target)
          ];
          state.activeSingleCopyWallet = modelSingleCopyWallet();
          renderSingleCopyModalContent();
          renderCopySections(state.wallets || []);
        }
      })
      .catch(err => console.warn('model single live refresh failed', err));
  }
}

function closeSingleCopyModal() {
  state.activeSingleCopyWallet = null;
  state.singleCopyCloseDialogOpen = false;
  state.singleCopyCloseWithdrawAddress = '';
  state.singleCopyCloseConfirmArmed = false;

  const card = document.querySelector('#traderModal .modal-card');
  if (card) card.classList.remove('single-copy-modal-card');

  closeModal('traderModal');
}

function openSingleCopyCloseDialog() {
  state.singleCopyCloseDialogOpen = true;
  state.singleCopyCloseWithdrawAddress = '';
  state.singleCopyCloseConfirmArmed = false;
  renderSingleCopyModalContent();
  setTimeout(() => {
    const input = document.getElementById('singleCopyWithdrawInput');
    if (input) input.focus();
  }, 0);
}

function closeSingleCopyCloseDialog() {
  state.singleCopyCloseDialogOpen = false;
  state.singleCopyCloseWithdrawAddress = '';
  state.singleCopyCloseConfirmArmed = false;
  renderSingleCopyModalContent();
}

async function confirmSingleCopyCloseFromDialog() {
  const input = document.getElementById('singleCopyWithdrawInput');
  const value = String(input?.value || '').trim();
  if (!isValidWallet(value)) {
    alert('Enter a valid wallet address starting with 0x.');
    if (input) input.focus();
    return;
  }

  if (!state.singleCopyCloseConfirmArmed) {
    state.singleCopyCloseWithdrawAddress = value;
    state.singleCopyCloseConfirmArmed = true;
    renderSingleCopyModalContent();
    setTimeout(() => {
      const confirmBtn = document.getElementById('confirmSingleCopyCloseBtn');
      if (confirmBtn) confirmBtn.focus();
    }, 0);
    return;
  }

  const wallet = state.activeSingleCopyWallet || {};
  const id = wallet.id;
  if (!id) {
    alert('Missing wallet id.');
    return;
  }

  const confirmBtn = document.getElementById('confirmSingleCopyCloseBtn');
  if (confirmBtn) {
    confirmBtn.disabled = true;
    confirmBtn.textContent = 'Closing...';
  }

  try {
    if (wallet.is_model_single_copy || String(id) === 'model-single-copy-slot') {
      ensureUiState();
      state.closedVaults.add('model-single-copy-slot');
      saveClosedVaults();
    } else {
      await api(`/api/wallets/${id}`, { method: 'DELETE' });
      state.wallets = (state.wallets || []).filter(w => String(w.id) !== String(id));
    }

    closeSingleCopyModal();
    renderCopySections(state.wallets || []);
    renderMultiLeaderboard(state.pools || [], state.wallets || []);
    if (!(wallet.is_model_single_copy || String(id) === 'model-single-copy-slot')) {
      await loadAll();
    }
  } catch (err) {
    console.error(err);
    alert(`Close failed: ${err.message || err}`);
    if (confirmBtn) {
      confirmBtn.disabled = false;
      confirmBtn.textContent = 'Confirm Close Copytrading';
    }
  }
}

function bindSingleCopyCloseDialog() {
  document.querySelectorAll('[data-single-copy-close-cancel], [data-single-copy-close-backdrop]').forEach(el => {
    el.addEventListener('click', (e) => {
      if (e.target !== el && el.dataset.singleCopyCloseBackdrop) return;
      closeSingleCopyCloseDialog();
    });
  });

  const input = document.getElementById('singleCopyWithdrawInput');
  if (input) {
    input.addEventListener('input', () => {
      state.singleCopyCloseWithdrawAddress = input.value.trim();
      if (state.singleCopyCloseConfirmArmed) {
        state.singleCopyCloseConfirmArmed = false;
        renderSingleCopyModalContent();
      }
    });
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') confirmSingleCopyCloseFromDialog();
      if (e.key === 'Escape') closeSingleCopyCloseDialog();
    });
  }

  const confirmBtn = document.getElementById('confirmSingleCopyCloseBtn');
  if (confirmBtn) {
    confirmBtn.addEventListener('click', confirmSingleCopyCloseFromDialog);
  }
}



const MODEL_SINGLE_COPY_ADDRESS = '0x0baFb25EF191bFe7A2727E14F5BbfC36610EC62A';

function modelSinglePositionRowsFromSource(source) {
  const positions = Array.isArray(source?.positions) ? source.positions : [];
  return positions.map((p, idx) => {
    const notional = Math.abs(Number(p.actual_notional || p.notional || p.target_notional || 0));
    const pnl = Number(p.pnl || p.unrealized_pnl || 0);
    const drift = Number(p.drift_pct || 0);
    return {
      id: `model-${idx}`,
      coin: p.coin || p.symbol || '?',
      side: p.side || 'Long',
      target_notional: Number(p.target_notional || notional),
      actual_notional: Number(p.actual_notional || notional),
      drift_pct: drift,
      pnl,
      pnl_pct: Number(p.pnl_pct || 0),
      entry: p.entry || p.entry_px || p.entry_price,
      mark: p.mark || p.live_price || p.display_price,
      liq_price: p.liq_price || p.liquidation_price || p.liq,
      icon_url: p.icon_url,
      dex: p.dex,
    };
  });
}

function modelSingleCopySourceRow() {
  const target = MODEL_SINGLE_COPY_ADDRESS.toLowerCase();
  const vaultRow = (state.fatbotVaults || []).find(v => String(v.address || '').toLowerCase() === target);
  if (vaultRow) return vaultRow;

  const traderRow = (state.traders || []).find(v => String(v.address || '').toLowerCase() === target);
  if (traderRow) return traderRow;

  const defaultRow = defaultVaultSourceRow();
  if (defaultRow && String(defaultRow.address || '').toLowerCase() === target) return defaultRow;

  return {};
}

function modelSingleCopyWallet() {
  const source = modelSingleCopySourceRow();
  const accountValue = Number(source.account_value || source.value || 0);
  const totalPnl = Number(source.total_pnl || source.pnl_usd || source.pnl_30d || 0);
  const positions = modelSinglePositionRowsFromSource(source);
  return {
    id: 'model-single-copy-slot',
    wallet_address: MODEL_SINGLE_COPY_ADDRESS,
    copied_trader_address: MODEL_SINGLE_COPY_ADDRESS,
    label: 'Model Single Copy',
    mode: 'single',
    status: 'active',
    is_model_single_copy: true,
    value: accountValue,
    available: Number(source.available || accountValue * 0.38 || 0),
    total_pnl: totalPnl,
    realized_pnl: Number(source.realized_pnl || 0),
    unrealized_pnl: Number(source.unrealized_pnl || totalPnl),
    gross_exposure: Number(source.gross_exposure || 0),
    net_exposure: Number(source.net_exposure || 0),
    drift: Number(source.drift || 0.0),
    positions,
    settings: {
      multiplier: 1,
      stop_drawdown_pct: -20,
      max_gross_exposure_pct: 150,
    },
    pnl_sparkline: source.pnl_sparkline || [],
    portfolio_chart_points: source.portfolio_chart_points || [],
  };
}

function isModelSingleCopyClosed() {
  // v171: model preview slot must always be visible for demo/live-output preview.
  return false;
}


function renderCopySections(wallets) {
  let single = wallets.filter(w => w.mode !== 'pool');
  if (isCopytradingView() && !isModelSingleCopyClosed()) {
    const model = modelSingleCopyWallet();
    single = [
      model,
      ...single.filter(w => String(w.wallet_address || '').toLowerCase() !== MODEL_SINGLE_COPY_ADDRESS.toLowerCase())
    ];
  }
  let multi = visibleVaultWallets(wallets || []);
  if (isFatBotVaultsView()) {
    const defaultWallet = defaultVaultWallet();
    multi = [
      defaultWallet,
      ...multi.filter(w => String(w.wallet_address || w.address || '').toLowerCase() !== DEFAULT_FATBOT_VAULT_ADDRESS.toLowerCase())
    ];
  }
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
  if ($('multiSectionText')) $('multiSectionText').textContent = 'Create or manage FatBot vault copy indexes. First 3 slots unlocked; more slots unlock by Perps volume.';
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
      const isExpanded = false;
      const isClosing = false;
      const extraMetricCol = type === 'multi'
        ? `<div class="vault-row-chart-col"><div class="row-sub">7D PnL</div>${vaultMiniChartHtml(w)}</div>`
        : `<div><div class="row-sub">Drift</div><strong>${Number(w.drift || 0).toFixed(1)}%</strong></div>`;
      const statusCol = type === 'multi' ? statusPulseDotHtml(w.status) : `<div class="status-badge ${w.status}">${String(w.status || '').toUpperCase()}</div>`;
      rows.push(`
        <div class="wallet-slot-wrap">
          <div class="wallet-row compact-wallet fixed-slot filled-slot ${type === 'multi' ? 'vault-wallet-row' : ''} ${w.is_default_vault ? 'default-fatbot-vault-row' : ''} ${w.is_model_single_copy ? 'model-single-copy-row' : ''}" data-wallet-id="${w.id}" data-wallet-mode="${w.mode}" data-default-vault="${w.is_default_vault ? '1' : ''}">
            <div class="slot-index">${i + 1}</div>
            ${copyWalletLogoHtml(w.mode)}
            <div>
              <div class="row-title">${w.label}</div>
              <div class="row-sub">${w.is_default_vault ? shortAddress(DEFAULT_FATBOT_VAULT_ADDRESS) : (w.mode === 'pool' ? 'Multi copy wallet' : `Copying: ${String(w.copied_trader_address || '').startsWith('vault:') ? 'Multi Vault' : shortAddress(w.copied_trader_address || 'Not selected')}`)}</div>
              <div class="progress"><i style="width:${Math.min(100, 35 + Number(w.gross_exposure || 0) * 25)}%"></i></div>
            </div>
            <div><div class="row-sub">Value</div><strong>${fmtUsd(w.value)}</strong></div>
            <div><div class="row-sub">Total PnL</div><strong class="${positiveClass(w.total_pnl)}">${fmtUsd(w.total_pnl)}</strong></div>
            <div><div class="row-sub">Exposure</div><strong>${Number(w.gross_exposure || 0).toFixed(2)}x</strong></div>
            ${extraMetricCol}
            ${statusCol}
          </div>
          ${type === 'single' && isExpanded ? walletExpandedPanel(w, isClosing) : ''}
        </div>
      `);
    } else {
      const slotNumber = i + 1;
      const lockedVaultSlot = type === 'multi' && slotNumber > unlockedVaultSlotLimit();
      const label = type === 'single' ? 'Start Single Copytrading' : 'Start FatBot Vault';
      if (lockedVaultSlot) {
        rows.push(`
          <div class="start-copy-card slot-card locked-vault-slot" data-locked-vault-slot="${slotNumber}" aria-disabled="true">
            <div class="locked-vault-blur-bg"></div>
            <div class="locked-vault-content">
              <span class="slot-index">${slotNumber}</span>
              <span class="locked-vault-lock">🔒</span>
              <div class="locked-vault-message">${vaultSlotUnlockText(slotNumber)}</div>
            </div>
          </div>
        `);
      } else {
        const inlineBuilder = type === 'multi' && Number(state.activeVaultBuilderSlot || 0) === slotNumber
          ? inlineVaultBuilderHtml(slotNumber)
          : '';
        rows.push(`
          <div class="wallet-slot-wrap empty-wallet-slot-wrap">
            <button class="start-copy-card slot-card" data-start-copy="${type}" data-slot="${slotNumber}">
              <span class="slot-index">${slotNumber}</span>
              ${copyWalletLogoHtml(type === 'multi' ? 'pool' : 'single')}
              <span class="plus-mark">+</span>
              <strong>${label}</strong>
            </button>
            ${inlineBuilder}
          </div>
        `);
      }
    }
  }

  el.innerHTML = rows.join('');

  el.querySelectorAll('[data-start-copy]').forEach(startBtn => {
    startBtn.addEventListener('click', () => {
      const selectedType = startBtn.dataset.startCopy;
      if (selectedType === 'single') {
        openSlotSettings('single', Number(startBtn.dataset.slot || 1));
      } else {
        state.selectedMultiTraders = ['', '', ''];
        state.vaultName = '';
        openInlineVaultBuilder(Number(startBtn.dataset.slot || 1));
      }
    });
  });

  el.querySelectorAll('[data-wallet-id]').forEach(row => {
    row.addEventListener('click', (e) => {
      if (e.target.closest('button') || e.target.closest('input') || e.target.closest('a')) return;
      const id = String(row.dataset.walletId);
      const wallet = wallets.find(item => String(item.id) === id) || (row.dataset.defaultVault === '1' ? defaultVaultWallet() : null);
      if (type === 'multi' || row.dataset.walletMode === 'pool' || row.dataset.defaultVault === '1') {
        openDefaultVaultModal(wallet || defaultVaultWallet());
        return;
      }
      openSingleCopyModal(wallet);
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

  bindInlineVaultBuilder();

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
      ${coinIconHtml(p.coin, p.icon_url || tokenIconUrl(p.coin, p.dex), p.dex)}
      <div><div class="row-title coin-side ${sideClass(p.side)}">${displayCoinLabel(p.coin)}</div><div class="row-sub">${p.side}</div></div>
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

function hotWalletCopiedUsers(item, index = 0) {
  const key = String(item?.vault_id || item?.address || item?.label || index);
  let hash = 0;
  for (let i = 0; i < key.length; i += 1) hash = ((hash << 5) - hash) + key.charCodeAt(i);
  return 18 + (Math.abs(hash) % 230);
}

function hotWalletVaultActivity(item, index = 0) {
  const key = String(item?.vault_id || item?.address || item?.label || index);
  let hash = 0;
  for (let i = 0; i < key.length; i += 1) hash = ((hash << 5) - hash) + key.charCodeAt(i);
  return 3 + (Math.abs(hash) % 42);
}

function buildHotWalletRows(pools = [], wallets = []) {
  const maxRows = 12;

  if (isCopytradingView()) {
    const traderRows = (state.traders || []).slice(0, 8).map((item, index) => ({
      ...item,
      hot_kind: 'wallet',
      hot_metric_label: 'Copied by users',
      hot_metric_value: hotWalletCopiedUsers(item, index),
      hot_sort_value: hotWalletCopiedUsers(item, index),
    }));

    const indexRows = (state.fatbotVaults || []).slice(0, 4).map((item, index) => ({
      ...item,
      hot_kind: 'index',
      hot_metric_label: 'Copied by users',
      hot_metric_value: hotWalletCopiedUsers(item, index + 100),
      hot_sort_value: hotWalletCopiedUsers(item, index + 100),
    }));

    return [...traderRows, ...indexRows]
      .sort((a, b) => Number(b.hot_sort_value || 0) - Number(a.hot_sort_value || 0))
      .slice(0, maxRows);
  }

  const vaultRows = (state.fatbotVaults || []).map((item, index) => ({
    ...item,
    hot_kind: 'vault',
    hot_metric_label: 'Active in FatBot Vaults',
    hot_metric_value: hotWalletVaultActivity(item, index),
    hot_sort_value: hotWalletVaultActivity(item, index),
  }));

  const poolRows = (pools || []).map((pool, index) => {
    const wallet = (wallets || []).find(w => Number(w.pool_id) === Number(pool.id)) || (wallets || []).find(w => Number(w.id) === Number(pool.wallet_id)) || {};
    const members = pool.members || [];
    return {
      ...wallet,
      address: wallet.wallet_address || wallet.address || `pool-${pool.id}`,
      label: pool.name || `FatBot Vault #${pool.id}`,
      source: 'fatbot_vault',
      vault_id: `pool-${pool.id}`,
      total_pnl: Number(wallet.total_pnl || 0),
      pnl_30d: Number(wallet.total_pnl || 0),
      account_value: Number(wallet.value || 0),
      copied_members: members,
      hot_kind: 'vault',
      hot_metric_label: 'Active in FatBot Vaults',
      hot_metric_value: Math.max(members.length || 0, hotWalletVaultActivity(pool, index)),
      hot_sort_value: Math.max(members.length || 0, hotWalletVaultActivity(pool, index)),
    };
  });

  return [...vaultRows, ...poolRows]
    .sort((a, b) => Number(b.hot_sort_value || 0) - Number(a.hot_sort_value || 0))
    .slice(0, maxRows);
}

function hotWalletSubtitle() {
  return isCopytradingView()
    ? 'Wallets and indexes most copied by users.'
    : 'Wallets currently active inside FatBot Vaults.';
}


function renderMultiLeaderboard(pools, wallets) {
  const el = safeClassRemove('multiLeaderboard', 'loading');
  if (!el) return;

  const title = document.getElementById('hotWalletsTitle');
  const subtitle = document.getElementById('hotWalletsSubtitle');
  if (title) title.textContent = 'Hot wallets';
  if (subtitle) subtitle.textContent = hotWalletSubtitle();

  const rows = buildHotWalletRows(pools || [], wallets || []);

  if (!rows.length) {
    el.innerHTML = `
      <div class="empty-state compact-empty">
        No hot wallets yet. Data will appear here after leaderboard and copy wallet data loads.
      </div>
    `;
    return;
  }

  el.innerHTML = rows.map((t, i) => {
    const isVault = t.source === 'fatbot_vault' || t.hot_kind === 'vault' || t.hot_kind === 'index';
    const isLive = isHydro(t) || isVault;
    const title = isVault ? (t.label || shortAddress(t.address)) : shortAddress(t.address);
    const subtitle = isVault
      ? (t.hot_kind === 'index' ? 'FatBot index / vault' : 'FatBot Vault')
      : 'Hydromancer PnL leaderboard';
    const actionLabel = isFatBotVaultAddMode() && !isVault ? 'Add to vault' : (isVault ? 'Copy Vault' : 'Copy Wallet');
    const copyTarget = t.address || t.wallet_address || t.vault_id;

    return `
      <div class="trader-row hydro-trader-row hot-wallet-row ${isVault ? 'fatbot-vault-row' : ''}" data-hot-address="${copyTarget}" data-hot-vault="${isVault ? '1' : ''}">
        ${leaderLogoHtml(t, i)}
        <div class="hot-wallet-main">
          <div class="row-title">${title}</div>
          <div class="row-sub">${subtitle}</div>
        </div>
        <div class="hot-wallet-metric">
          <div class="row-sub">${t.hot_metric_label || (isCopytradingView() ? 'Copied by users' : 'Active in FatBot Vaults')}</div>
          <strong>${Number(t.hot_metric_value || 0).toLocaleString()}</strong>
        </div>
        <div class="hot-wallet-pnl">
          <div class="row-sub">PnL</div>
          <strong class="${positiveClass(pnlNumber(t))}">${pnlDisplay(t)}</strong>
        </div>
        <button class="copy-btn small-copy" data-hot-copy="${copyTarget}" data-hot-vault-copy="${isVault ? '1' : ''}">${actionLabel}</button>
      </div>
    `;
  }).join('');

  el.querySelectorAll('.hot-wallet-row').forEach(row => {
    row.addEventListener('click', (e) => {
      if (e.target.dataset.hotCopy) return;
      const address = row.dataset.hotAddress;
      if (!row.dataset.hotVault || row.dataset.hotVault !== '1') {
        openTrader(address);
      }
    });
  });

  el.querySelectorAll('[data-hot-copy]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (isFatBotVaultAddMode() && btn.dataset.hotVaultCopy !== '1') {
        addTraderToVaultBuilder(btn.dataset.hotCopy);
      } else {
        openCopyWizard(btn.dataset.hotCopy);
      }
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
      ${coinIconHtml(p.coin, p.icon_url || tokenIconUrl(p.coin, p.dex), p.dex)}
      <div><div class="row-title">${displayCoinLabel(p.coin)}</div><div class="row-sub">${p.wallet_label} · ${p.side}</div></div>
      <div><div class="row-sub">Actual</div><strong>${fmtUsd(p.actual_notional)}</strong></div>
      <div><div class="row-sub">Drift</div><strong class="${positiveClass(p.drift_pct)}">${fmtPct(p.drift_pct)}</strong></div>
      <div><div class="row-sub">PnL</div><strong class="${positiveClass(p.pnl)}">${fmtUsd(p.pnl)}</strong></div>
      <div><div class="row-sub">PnL</div><strong class="${positiveClass(p.pnl_pct)}">${fmtPct(p.pnl_pct)}</strong></div>
    </div>
  `).join('');
}

function renderMoves(positions) {
  const el = $('movesList');
  if (!el) return;
  const items = positions.slice(0, 3);
  el.innerHTML = items.map(p => `
    <div class="move-row">
      <span>${displayCoinLabel(p.coin)} ${String(p.side || '').toLowerCase()} copied</span>
      <strong class="${positiveClass(p.pnl)}">${fmtUsd(p.pnl)}</strong>
    </div>
  `).join('') || `
    <div class="move-row"><span>No recent execution moves.</span><strong>$0.00</strong></div>
  `;
}

function mergeTraderPreviewFields(trader, preview) {
  if (!trader || !preview) return trader;

  const merged = { ...trader };
  const keys = [
    'account_value',
    'account_value_source',
    'rank',
    'total_pnl',
    'pnl_30d',
    'pnl_90d',
    'volume',
    'volume_traded',
    'win_rate',
    'total_trades',
    'trades',
    'days_active',
    'account_age_days',
    'total_funding',
    'funding',
  ];

  keys.forEach(key => {
    const current = merged[key];
    const incoming = preview[key];
    const missing = current === undefined || current === null || current === '' || current === 0 || current === '0';
    const hasIncoming = incoming !== undefined && incoming !== null && incoming !== '' && incoming !== 0 && incoming !== '0';
    if (missing && hasIncoming) merged[key] = incoming;
  });

  merged.merged_preview_row = true;
  return merged;
}


async function chartFormatTime(ts) {
  const n = Number(ts || 0);
  if (!Number.isFinite(n) || n <= 0) return '';
  const ms = n > 100000000000 ? n : n > 1000000000 ? n * 1000 : n;
  const d = new Date(ms);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

function profileChartPoints(trader) {
  const points = Array.isArray(trader?.portfolio_chart_points) ? trader.portfolio_chart_points : [];
  if (points.length >= 2) return points;

  // Fallback: use the same real PnL points already shown by the mini leaderboard sparkline.
  // This keeps the large PnL chart visible even when the slower full portfolio chart attach is missing.
  const spark = Array.isArray(trader?.pnl_sparkline)
    ? trader.pnl_sparkline.map(Number).filter(Number.isFinite)
    : [];
  if (spark.length < 2) return [];

  return spark.map((value, idx) => ({
    ts: idx + 1,
    pnl_usd: value,
  }));
}


function profileChartOptions(trader) {
  const points = profileChartPoints(trader);
  const hasSeries = key => points.filter(p => Number.isFinite(Number(p?.[key]))).length >= 2;

  const out = [];
  if (hasSeries('pnl_usd')) {
    out.push({
      key: 'pnl_usd',
      label: 'PnL USD',
      title: 'PnL USD',
      formatter: fmtUsd,
      description: 'Hyperliquid portfolio pnlHistory'
    });
  }
  if (hasSeries('account_value')) {
    out.push({
      key: 'account_value',
      label: 'Account Value',
      title: 'Account Value',
      formatter: fmtUsd,
      description: 'Hyperliquid portfolio accountValueHistory'
    });
  }
  if (hasSeries('pnl_equity_pct')) {
    out.push({
      key: 'pnl_equity_pct',
      label: 'PnL / Equity %',
      title: 'PnL / Equity %',
      formatter: value => `${Number(value).toFixed(2)}%`,
      description: 'pnl_usd / account_value × 100. Not cashflow-adjusted ROI.'
    });
  }
  return out;
}

function profileSingleChartInnerHtml(trader, key) {
  const points = profileChartPoints(trader);
  const options = profileChartOptions(trader);
  const option = options.find(o => o.key === key) || options[0];

  if (!option) {
    return `<div class="profile-chart-empty">Not enough chart data</div>`;
  }

  const rows = points.filter(p => Number.isFinite(Number(p?.[option.key])));
  if (rows.length < 2) {
    return `<div class="profile-chart-empty">Not enough ${option.label} data</div>`;
  }

  const width = 980;
  const height = 300;
  const padX = 18;
  const padY = 22;
  const values = rows.map(p => Number(p[option.key]));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = Math.max(max - min, 1e-9);

  const pointString = rows.map((p, index) => {
    const x = padX + (index / (rows.length - 1)) * (width - padX * 2);
    const y = height - padY - ((Number(p[option.key]) - min) / range) * (height - padY * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');

  const first = values[0];
  const last = values[values.length - 1];
  const delta = last - first;
  const deltaClass = option.key === 'pnl_equity_pct' ? (last >= 0 ? 'positive' : 'negative') : (delta >= 0 ? 'positive' : 'negative');
  const startLabel = chartFormatTime(rows[0]?.ts);
  const endLabel = chartFormatTime(rows[rows.length - 1]?.ts);

  return `
    <div class="profile-chart-active-head">
      <div>
        <h3>${option.title}</h3>
        <p>${option.description}</p>
      </div>
      <div class="profile-chart-active-value">
        <strong class="${deltaClass}">${option.formatter(last)}</strong>
        <span>${startLabel && endLabel ? `${startLabel} → ${endLabel}` : `${rows.length} points`}</span>
      </div>
    </div>
    <svg class="profile-line-chart ${deltaClass} ${option.key === 'pnl_equity_pct' ? 'yellow-chart' : ''}" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-hidden="true">
      <line x1="${padX}" y1="${height - padY}" x2="${width - padX}" y2="${height - padY}" />
      <line x1="${padX}" y1="${padY}" x2="${width - padX}" y2="${padY}" />
      <polyline points="${pointString}" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"></polyline>
    </svg>
    <div class="profile-chart-foot">
      <span>Min ${option.formatter(min)}</span>
      <span>Max ${option.formatter(max)}</span>
    </div>
  `;
}

function profileChartsHtml(trader) {
  const options = profileChartOptions(trader);
  if (!options.length) return '';

  const windowLabel = trader.portfolio_chart_window ? String(trader.portfolio_chart_window).toUpperCase() : '30D';
  const defaultKey = options[0].key;

  return `
    <div class="profile-chart-section profile-chart-section-top">
      <div class="profile-chart-topline">
        <div>
          <span class="pill">PORTFOLIO CHART</span>
          <h3>${windowLabel} wallet history</h3>
          <p>One chart at a time. PnL / Equity % is not cashflow-adjusted ROI.</p>
        </div>
      </div>
      <div class="profile-chart-single-card">
        <div id="profileActiveChart" data-active-chart="${defaultKey}">
          ${profileSingleChartInnerHtml(trader, defaultKey)}
        </div>
        <div class="profile-chart-toggle profile-chart-toggle-bottom" role="tablist">
          ${options.map((o, idx) => `
            <button type="button" class="profile-chart-toggle-btn ${idx === 0 ? 'active' : ''}" data-profile-chart="${o.key}">
              ${o.label}
            </button>
          `).join('')}
        </div>
      </div>
    </div>
  `;
}

function bindProfileChartToggle(trader) {
  const box = document.getElementById('profileActiveChart');
  const buttons = document.querySelectorAll('[data-profile-chart]');
  if (!box || !buttons.length) return;

  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      const key = btn.dataset.profileChart;
      box.dataset.activeChart = key;
      box.innerHTML = profileSingleChartInnerHtml(trader, key);

      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });
}




async function openTrader(address) {
  const el = document.getElementById('traderModalContent');

  const preview = [...(state.traders || []), ...(state.fatbotVaults || [])].find(t => String(t.address || '').toLowerCase() === String(address || '').toLowerCase());
  const previewTitle = walletDisplayName(preview || address);

  el.innerHTML = `
    <button class="profile-back-btn" data-profile-back="1" title="Back">←</button>
    <div class="wizard-head trader-profile-head with-back-button">
      <div>
        <span class="pill">TRADER PROFILE</span>
        <div style="display:flex; align-items:center; gap:12px; margin-top:10px;">
          ${preview ? leaderLogoHtml(preview, 0, 'profile-provider-logo') : `<div class="avatar-badge alt-a">${traderBadgeLabel(address)}</div>`}
          <div>
            <div class="profile-wallet-title-row">
              <h2 style="margin:0;">${previewTitle}</h2>
              <button class="wallet-icon-btn profile-wallet-action" data-rename-wallet="${address}" title="Rename wallet">✎</button>
              <a class="wallet-icon-btn wallet-link-btn profile-wallet-action" data-wallet-link="1" href="${hypurrscanAddressUrl(address)}" target="_blank" rel="noopener noreferrer" title="Open on Hypurrscan">${externalLinkIconSvg()}</a>
            </div>
            <p class="muted" style="margin:4px 0 0;">${shortAddress(address)}</p>
          </div>
        </div>
      </div>
      <button class="primary trader-head-copy" data-modal-copy="${address}">COPY THIS TRADER</button>
    </div>
    <div class="profile-loading-card">
      <div class="mini-spinner"></div>
      <div>
        <strong>Loading live profile...</strong>
        <p class="muted">Opening cached profile and live state.</p>
      </div>
    </div>
  `;

  const loadingBackBtn = el.querySelector('[data-profile-back]');
  if (loadingBackBtn) loadingBackBtn.addEventListener('click', () => closeModal('traderModal'));
  el.querySelectorAll('[data-rename-wallet]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      renameWalletAlias(btn.dataset.renameWallet);
      const title = el.querySelector('.profile-wallet-title-row h2');
      if (title) title.textContent = walletDisplayName(btn.dataset.renameWallet);
    });
  });
  el.querySelectorAll('[data-wallet-link]').forEach(link => {
    link.addEventListener('click', (e) => e.stopPropagation());
  });
  el.querySelector('[data-modal-copy]').addEventListener('click', () => {
    closeModal('traderModal');
    openCopyWizard(address);
  });
  openModal('traderModal');

  let trader;
  try {
    trader = await api(`/api/traders/${encodeURIComponent(address)}?${leaderboardQueryString()}`);
  } catch (err) {
    if (preview) {
      trader = {
        ...preview,
        history: [],
        profile_mode: 'frontend_visible_row_fallback',
        profile_warning: `Profile API failed: ${err.message || err}. Showing the exact visible leaderboard row. If this row has no positions, the backend profile lookup still needs debugging.`,
      };
    } else {
      el.innerHTML += `<div class="empty-state">Failed to load trader profile: ${err.message || err}<br><small>Try refreshing the leaderboard once; this can happen if the filtered scan cache changed.</small></div>`;
      return;
    }
  }

  trader = mergeTraderPreviewFields(trader, preview);

  state.selectedTrader = trader;
  const isLive = isHydro(trader) || trader.source === 'fatbot_vault';
  const positions = Array.isArray(trader.positions) ? trader.positions : [];

  const liveCards = isLive ? `
      <div class="detail-card"><span>${trader.source === "fatbot_vault" ? `${String((state.leaderboardFilters || {}).window || "30d").toUpperCase()} PnL` : `PnL Window (${String((state.leaderboardFilters || {}).window || "30d").toUpperCase()})`}</span><strong class="${positiveClass(trader.source === "fatbot_vault" ? (trader.pnl_pct ?? trader.pnl_30d) : trader.total_pnl)}">${fmtUsd(pnlUsdValue(trader))}</strong></div>
      <div class="detail-card"><span>Account Value</span><strong>${moneyOrDash(trader.account_value)}</strong></div>
      <div class="detail-card"><span>Long / Short</span><strong>${exposureShareDisplay(trader)}</strong></div>
      <div class="detail-card"><span>Gross Exposure</span><strong>${grossExposureDisplay(trader)}</strong></div>
      <div class="detail-card"><span>30D Win Rate</span><strong>${winRateDisplay(trader)}</strong></div>
      <div class="detail-card"><span>30D Trades</span><strong>${Number(trader.total_trades || trader.trades || 0).toLocaleString()}</strong></div>
      <div class="detail-card"><span>Account Age</span><strong>${Number(trader.account_age_days || 0)} days</strong></div>
      <div class="detail-card"><span>30D Volume</span><strong>${fmtUsd(trader.volume || trader.volume_traded || 0)}</strong></div>
      <div class="detail-card"><span>Live Positions</span><strong>${Number(trader.open_positions || 0)}</strong></div>
  ` : `
      <div class="detail-card"><span>30D PnL</span><strong class="${positiveClass(trader.pnl_30d)}">${fmtPct(trader.pnl_30d)}</strong></div>
      <div class="detail-card"><span>90D PnL</span><strong class="${positiveClass(trader.pnl_90d)}">${fmtPct(trader.pnl_90d)}</strong></div>
      <div class="detail-card"><span>Volume</span><strong>${fmtUsd(trader.volume || 0)}</strong></div>
      <div class="detail-card"><span>Open Positions</span><strong>${trader.open_positions || 0}</strong></div>
      <div class="detail-card"><span>Win Rate</span><strong>${winRateDisplay(trader)}</strong></div>
  `;

  const traderDisplayName = walletDisplayName(trader);

  el.innerHTML = `
    <button class="profile-back-btn" data-profile-back="1" title="Back">←</button>
    <div class="wizard-head trader-profile-head profile-head-top with-back-button">
      <div>
        <span class="pill">TRADER PROFILE</span>
        <div style="display:flex; align-items:center; gap:12px; margin-top:10px;">
          ${leaderLogoHtml(trader, 0, 'profile-provider-logo')}
          <div>
            <div class="profile-wallet-title-row">
              <h2 style="margin:0;">${traderDisplayName}</h2>
              <button class="wallet-icon-btn profile-wallet-action" data-rename-wallet="${trader.address}" title="Rename wallet">✎</button>
              <a class="wallet-icon-btn wallet-link-btn profile-wallet-action" data-wallet-link="1" href="${hypurrscanAddressUrl(trader.address)}" target="_blank" rel="noopener noreferrer" title="Open on Hypurrscan">${externalLinkIconSvg()}</a>
            </div>
            <p class="muted" style="margin:4px 0 0;">${shortAddress(trader.address)}</p>
            ${isLive ? '' : `<p>${trader.label}</p>`}
          </div>
        </div>
      </div>
      <button class="primary trader-head-copy" data-modal-copy="${trader.address}">COPY THIS TRADER</button>
    </div>

    ${profileChartsHtml(trader)}

    ${trader.profile_warning ? `<div class="empty-state profile-warning-box">${trader.profile_warning}</div>` : ''}

    <div class="detail-grid hydro-detail-grid">
      ${liveCards}
    </div>

    <div class="panel-head small" style="margin-top:18px;">
      <h3>${isLive ? 'Live Hyperliquid positions' : 'Open positions'}</h3>
    </div>

    <div class="position-list">
      ${positions.length ? positions.map(p => `
        <div class="position-row trader-live-position-row">
          ${coinIconHtml(p.coin, p.icon_url, p.dex)}
          <div><div class="row-title coin-side ${sideClass(p.side)}">${displayCoinLabel(p.coin)}</div><div class="row-sub">${p.side} · ${Number(p.leverage || 0).toFixed(1)}x</div></div>
          <div><div class="row-sub">Notional</div><strong>${fmtUsd(p.notional)}</strong></div>
          <div><div class="row-sub">Entry</div><strong>${p.entry ? Number(p.entry).toLocaleString(undefined, { maximumFractionDigits: 6 }) : "—"}</strong></div>
          <div><div class="row-sub">Live Price</div><strong>${fmtLivePrice(p.live_price || p.display_price)}</strong></div>
          <div><div class="row-sub">PnL</div><strong class="${positiveClass(p.pnl)}">${fmtUsd(p.pnl)}</strong></div>
          <div><div class="row-sub">Liq</div><strong>${fmtLivePrice(p.liq_price)}</strong></div>
        </div>
      `).join('') : `<p class="muted">${isLive ? 'No position rows were returned by the profile endpoint. This is a data-fetch diagnostic state, not a confirmed zero-position result.' : 'No live positions available for this trader yet.'}</p>`}
    </div>
  `;

  bindProfileChartToggle(trader);

  const profileBackBtn = el.querySelector('[data-profile-back]');
  if (profileBackBtn) profileBackBtn.addEventListener('click', () => closeModal('traderModal'));

  el.querySelectorAll('[data-rename-wallet]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      renameWalletAlias(btn.dataset.renameWallet);
      const title = el.querySelector('.profile-wallet-title-row h2');
      if (title) title.textContent = walletDisplayName(btn.dataset.renameWallet);
    });
  });
  el.querySelectorAll('[data-wallet-link]').forEach(link => {
    link.addEventListener('click', (e) => e.stopPropagation());
  });

  el.querySelector('[data-modal-copy]').addEventListener('click', () => {
    closeModal('traderModal');
    openCopyWizard(trader.address);
  });
}


function openSlotSettings(mode, slot) {
  const copyModal = document.getElementById('copyModal');
  if (copyModal) copyModal.classList.remove('direct-copy-modal');
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
    if (multiCount >= unlockedVaultSlotLimit()) {
      showMultiSlotsFullAlert();
      return;
    }
    if (Number(slot || 1) > unlockedVaultSlotLimit()) {
      alert(vaultSlotUnlockText(slot));
      return;
    }
    state.selectedTrader = null;
    if (!state.vaultName) state.vaultName = `FatBot Vault #${slot}`;
    if (!Array.isArray(state.selectedMultiTraders) || state.selectedMultiTraders.length === 0) {
      state.selectedMultiTraders = ['', '', ''];
    }
    document.getElementById('copyModalTrader').textContent = `FatBot Vaults · Slot #${slot}`;
  }

  renderWizard();
  openModal('copyModal');
}




function singleWalletCount() {
  return state.wallets.filter(w => w.mode !== 'pool').length;
}

function visibleVaultWallets(wallets = state.wallets || []) {
  return (wallets || []).filter(w => w.mode === 'pool' && !isVaultClosed(w) && !isRemovedPresetVault(w));
}

function upsertWalletInState(wallet) {
  if (!wallet || !wallet.id) return;
  const id = String(wallet.id);
  const without = (state.wallets || []).filter(w => String(w.id) !== id);
  state.wallets = [wallet, ...without];
}

function multiWalletCount() {
  return visibleVaultWallets(state.wallets || []).length;
}

function showSingleSlotsFullAlert() {
  alert(`Single Copytrading slots are full: ${singleSlotLimit()}/${singleSlotLimit()}. Close or delete one single copytrading wallet before creating another one.`);
}

function showMultiSlotsFullAlert() {
  alert(`The first ${unlockedVaultSlotLimit()} FatBot Vault slots are full. Close one vault or unlock more slots by Perps volume.`);
}

function openVaultCopySettings(pool) {
  const copyModal = document.getElementById('copyModal');
  if (copyModal) copyModal.classList.remove('direct-copy-modal');
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
  document.getElementById('copyModalTrader').textContent = `Copying: ${shortAddress(address)}`;
  const copyModal = document.getElementById('copyModal');
  if (copyModal) copyModal.classList.add('direct-copy-modal');
  const copyModalTitle = document.querySelector('#copyModal .wizard-head h2');
  if (copyModalTitle) copyModalTitle.textContent = 'Create Copytrading Wallet';
  renderWizard();
  openModal('copyModal');
}


function singleCopyTopChartHtml(trader) {
  const options = profileChartOptions(trader).filter(o => o.key === 'pnl_usd');
  const option = options[0];
  if (!option) {
    return `
      <div class="copy-source-chart-card empty">
        <div class="profile-chart-empty">No 30D PnL chart data for this wallet yet</div>
      </div>
    `;
  }

  return `
    <div class="copy-source-chart-card">
      <div class="copy-source-chart-head">
        <div>
          <span class="pill">30D PnL CHART</span>
          <h3>${walletDisplayName(trader)}</h3>
          <p>${shortAddress(trader.address)}</p>
        </div>
      </div>
      <div class="copy-source-chart-body">
        ${profileSingleChartInnerHtml(trader, 'pnl_usd')}
      </div>
    </div>
  `;
}

function singleCopySourceSummaryHtml(trader) {
  return `
    <div class="copy-source-metrics">
      <div class="detail-card"><span>Account Value</span><strong>${moneyOrDash(trader.account_value)}</strong></div>
      <div class="detail-card"><span>30D PnL</span><strong class="${positiveClass(pnlNumber(trader))}">${pnlDisplay(trader)}</strong></div>
      <div class="detail-card"><span>Gross Exposure</span><strong>${grossExposureDisplay(trader)}</strong></div>
    </div>
  `;
}

function singleCopyWalletNameRow() {
  return `
    <div class="form-row copy-wallet-name-row">
      <label>Copytrading name</label>
      <input id="singleWalletName" class="form-input" placeholder="Name your copytrading strategy" value="${state.singleWalletName || ''}" />
    </div>
  `;
}


function renderWizard() {
  const step = state.wizardStep;
  const el = document.getElementById('wizardStep');
  const next = document.getElementById('wizardNext');
  const back = document.getElementById('wizardBack');
  const isMulti = state.copySetupMode === 'multi';
  back.style.visibility = step === 0 ? 'hidden' : 'visible';

  if (step === 0) {
    next.textContent = state.copySetupMode === 'vault_single' ? 'Copy Vault' : (isMulti ? 'Create FatBot Vault' : 'Create and fund copytrading wallet');

    if (state.copySetupMode === 'vault_single') {
      const pool = state.selectedVaultToCopy;
      const members = (pool?.members || []).map(m => m.trader_address).slice(0, 10);
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
        ${rangeRow('Gross exposure multiplier', 'multiplier', 0.1, 10, 0.1, 'x')}
        ${drawdownRow()}
        ${marginInfoRow()}
        ${numberRow('Max gross exposure', 'max_gross_exposure_pct', '%')}
      `;
      bindWizardInputs();
      return;
    }

    if (isMulti) {
      next.textContent = 'Next steps';
      el.innerHTML = `
        <h3>Step 1: Add traders to vault</h3>
        <p class="muted">Add manual wallets here, or click Add to vault from the leaderboard on the left.</p>
        <div class="detail-grid">
          <div class="detail-card"><span>Mode</span><strong>FatBot Vault</strong></div>
          <div class="detail-card"><span>Vault slot</span><strong>#${state.selectedSlot || 1}</strong></div>
        </div>
        ${vaultNameRow()}
        ${vaultTraderSlotRows()}
      `;
      bindVaultName();
      bindVaultTraderSlots();
      return;
    }

    const copiedTrader = state.selectedTrader || {};
    next.textContent = 'Create and fund copytrading wallet';

    el.innerHTML = `
      <div class="single-copy-redesign">
        ${singleCopyTopChartHtml(copiedTrader)}

        <div class="copy-source-address-card">
          <div>
            <div class="copy-source-pill-row">
              <span class="pill">COPY SOURCE</span>
              <a class="wallet-icon-btn wallet-link-btn profile-wallet-action" data-wallet-link="1" href="${hypurrscanAddressUrl(copiedTrader.address)}" target="_blank" rel="noopener noreferrer" title="Open on Hypurrscan">${externalLinkIconSvg()}</a>
            </div>
            <h3>${walletDisplayName(copiedTrader)}</h3>
            <p>${shortAddress(copiedTrader.address)}</p>
          </div>
          ${singleCopyWalletNameRow()}
        </div>

        ${singleCopySourceSummaryHtml(copiedTrader)}

        <div class="copy-settings-block">
          <h3>Set your exposure multiplier</h3>
          ${rangeRow('Gross exposure multiplier', 'multiplier', 0.1, 10, 0.1, 'x')}
          ${drawdownRow()}
          ${marginInfoRow()}
        </div>
      </div>
    `;
    bindWizardInputs();
    bindSingleWalletName();
    el.querySelectorAll('[data-wallet-link]').forEach(link => {
      link.addEventListener('click', (e) => e.stopPropagation());
    });
  }

  if (step === 1 && isMulti) {
    next.textContent = 'Create and fund vault address';
    el.innerHTML = `
      <h3>Step 2: Vault risk settings</h3>
      <p class="muted">Set risk controls for this FatBot Vault.</p>
      <div class="detail-grid">
        <div class="detail-card"><span>Selected traders</span><strong>${selectedVaultTraderAddresses().length}</strong></div>
        <div class="detail-card"><span>Vault slot</span><strong>#${state.selectedSlot || 1}</strong></div>
      </div>
      <div class="copy-settings-block">
        ${rangeRow('Vault exposure multiplier', 'multiplier', 0.1, 10, 0.1, 'x')}
        ${drawdownRow()}
        ${marginInfoRow()}
      </div>
    `;
    bindWizardInputs();
    return;
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
        <div class="detail-card"><span>Gross exposure multiplier</span><strong>${state.wizardSettings.multiplier}x</strong></div>
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



function normalizeVaultTraderSlots() {
  if (!Array.isArray(state.selectedMultiTraders)) state.selectedMultiTraders = ['', '', ''];
  state.selectedMultiTraders = state.selectedMultiTraders.map(x => String(x || '').trim()).slice(0, 10);
  while (state.selectedMultiTraders.length < 3) state.selectedMultiTraders.push('');
  return state.selectedMultiTraders;
}

function selectedVaultTraderAddresses() {
  const seen = new Set();
  const out = [];
  normalizeVaultTraderSlots().forEach(addr => {
    const value = String(addr || '').trim();
    const key = value.toLowerCase();
    if (isValidWallet(value) && !seen.has(key)) {
      seen.add(key);
      out.push(value);
    }
  });
  return out;
}

function addTraderToVaultBuilder(address) {
  const value = String(address || '').trim();

  if (!document.getElementById('traderModal')?.classList.contains('hidden') && state.defaultVaultModalTab === 'management') {
    const modalWallet = activeVaultModalWallet();
    const members = getVaultModalMembers(modalWallet);
    if (isValidWallet(value) && !members.some(x => String(x).toLowerCase() === value.toLowerCase())) {
      members.push(value);
      setVaultModalMembers(modalWallet, members);
      renderDefaultVaultModalContent();
    }
    return;
  }
  if (!isValidWallet(value)) {
    alert('Invalid wallet address.');
    return;
  }

  if (!state.activeVaultBuilderSlot) {
    state.activeVaultBuilderSlot = Math.min(unlockedVaultSlotLimit(), multiWalletCount() + (isFatBotVaultsView() && !isVaultClosed(defaultVaultWallet()) ? 2 : 1));
    state.selectedSlot = state.activeVaultBuilderSlot;
    state.copySetupMode = 'multi';
    state.vaultBuilderStep = 0;
    state.vaultName = state.vaultName || `FatBot Vault #${state.selectedSlot}`;
    state.selectedMultiTraders = ['', '', ''];
  }

  normalizeVaultTraderSlots();
  const exists = state.selectedMultiTraders.some(x => String(x || '').toLowerCase() === value.toLowerCase());
  if (exists) {
    renderCopySections(state.wallets || []);
    return;
  }

  let index = state.selectedMultiTraders.findIndex(x => !String(x || '').trim());
  if (index < 0) {
    if (state.selectedMultiTraders.length >= 10) {
      alert('Maximum 10 traders per vault.');
      return;
    }
    state.selectedMultiTraders.push('');
    index = state.selectedMultiTraders.length - 1;
  }
  state.selectedMultiTraders[index] = value;
  renderCopySections(state.wallets || []);
}

function openInlineVaultBuilder(slot) {
  const slotNumber = Number(slot || 1);
  if (slotNumber > unlockedVaultSlotLimit()) {
    alert(vaultSlotUnlockText(slotNumber));
    return;
  }
  const effectiveVisibleVaultCount = multiWalletCount() + (isFatBotVaultsView() && !isVaultClosed(defaultVaultWallet()) ? 1 : 0);
  if (effectiveVisibleVaultCount >= unlockedVaultSlotLimit()) {
    showMultiSlotsFullAlert();
    return;
  }

  state.activeVaultBuilderSlot = slotNumber;
  state.selectedSlot = slotNumber;
  state.copySetupMode = 'multi';
  state.vaultBuilderStep = 0;
  state.vaultName = state.vaultName || `FatBot Vault #${slotNumber}`;
  if (!Array.isArray(state.selectedMultiTraders) || !state.selectedMultiTraders.length) {
    state.selectedMultiTraders = ['', '', ''];
  }
  renderCopySections(state.wallets || []);
}

function closeInlineVaultBuilder() {
  state.activeVaultBuilderSlot = null;
  state.vaultBuilderStep = 0;
  state.selectedMultiTraders = [];
  state.vaultName = '';
  renderCopySections(state.wallets || []);
}

function vaultTraderDropdownOptions(selected) {
  const current = String(selected || '').toLowerCase();
  const rows = (state.traders || []).slice(0, 50).map((t, idx) => {
    const addr = String(t.address || '');
    if (!addr) return '';
    const label = `#${idx + 1} ${walletDisplayName(t)} · ${shortAddress(addr)} · ${pnlDisplay(t)}`;
    return `<option value="${addr}" ${addr.toLowerCase() === current ? 'selected' : ''}>${label}</option>`;
  }).join('');
  return `<option value="">Select trader from leaderboard</option>${rows}`;
}

function vaultTraderSlotRows() {
  const slots = normalizeVaultTraderSlots();
  return `
    <div class="vault-trader-slot-list">
      ${slots.map((addr, idx) => `
        <div class="vault-trader-slot-row">
          <span class="slot-index">${idx + 1}</span>
          <input class="form-input vault-trader-input" data-vault-trader-index="${idx}" placeholder="Pick wallet from leaderboard or paste your own" value="${addr || ''}" />
          <button class="wallet-icon-btn" type="button" data-remove-vault-trader="${idx}" title="Clear trader slot">×</button>
        </div>
      `).join('')}
    </div>
    <button type="button" class="secondary add-trader-slot-btn" id="addVaultTraderSlot">add trader slot</button>
    <small class="muted">Minimum 3 traders, maximum 10 traders. Click Add to vault from the leaderboard or paste your own wallet address.</small>
  `;
}

function bindVaultTraderSlots() {
  document.querySelectorAll('[data-vault-trader-index]').forEach(input => {
    input.addEventListener('input', () => {
      normalizeVaultTraderSlots();
      const idx = Number(input.dataset.vaultTraderIndex || 0);
      state.selectedMultiTraders[idx] = input.value.trim();
    });
  });

  document.querySelectorAll('[data-remove-vault-trader]').forEach(btn => {
    btn.addEventListener('click', () => {
      normalizeVaultTraderSlots();
      const idx = Number(btn.dataset.removeVaultTrader || 0);
      state.selectedMultiTraders[idx] = '';
      renderCopySections(state.wallets || []);
    });
  });

  const addBtn = document.getElementById('addVaultTraderSlot');
  if (addBtn) {
    addBtn.addEventListener('click', () => {
      normalizeVaultTraderSlots();
      if (state.selectedMultiTraders.length >= 10) {
        alert('Maximum 10 traders per vault.');
        return;
      }
      state.selectedMultiTraders.push('');
      renderCopySections(state.wallets || []);
    });
  }
}

function inlineVaultBuilderHtml(slotNumber) {
  const step = Number(state.vaultBuilderStep || 0);
  if (step === 1) {
    return `
      <div class="inline-vault-builder" data-inline-vault-builder="${slotNumber}">
        <div class="inline-vault-head">
          <div>
            <span class="pill">FATBOT VAULT SETUP</span>
            <h3>Step 2: Vault risk settings</h3>
            <p class="muted">${selectedVaultTraderAddresses().length} selected traders · Slot #${slotNumber}</p>
          </div>
          <button class="wallet-icon-btn" type="button" data-close-inline-vault="1">×</button>
        </div>
        <div class="copy-settings-block">
          ${rangeRow('Vault exposure multiplier', 'multiplier', 0.1, 10, 0.1, 'x')}
          ${drawdownRow()}
          ${marginInfoRow()}
        </div>
        <div class="inline-vault-actions">
          <button class="secondary" type="button" data-vault-builder-back="1">Back</button>
          <button class="primary" type="button" data-create-inline-vault="1">Create and fund vault address</button>
        </div>
      </div>
    `;
  }

  return `
    <div class="inline-vault-builder" data-inline-vault-builder="${slotNumber}">
      <div class="inline-vault-head">
        <div>
          <span class="pill">FATBOT VAULT SETUP</span>
          <h3>Step 1: Add traders to vault</h3>
          <p class="muted">Pick wallets from the leaderboard or paste your own wallet addresses.</p>
        </div>
        <button class="wallet-icon-btn" type="button" data-close-inline-vault="1">×</button>
      </div>
      ${vaultNameRow()}
      ${vaultTraderSlotRows()}
      <div class="inline-vault-actions">
        <button class="primary" type="button" data-vault-builder-next="1">Next steps</button>
      </div>
    </div>
  `;
}

function bindInlineVaultBuilder() {
  bindVaultName();
  bindVaultTraderSlots();
  bindWizardInputs();

  document.querySelectorAll('[data-close-inline-vault]').forEach(btn => {
    btn.addEventListener('click', closeInlineVaultBuilder);
  });

  document.querySelectorAll('[data-vault-builder-next]').forEach(btn => {
    btn.addEventListener('click', () => {
      const selected = selectedVaultTraderAddresses();
      if (selected.length < 3) {
        alert('Add at least 3 valid trader wallets.');
        return;
      }
      if (selected.length > 10) {
        alert('Maximum 10 traders per vault.');
        return;
      }
      state.selectedMultiTraders = selected.slice(0, 10);
      state.vaultBuilderStep = 1;
      renderCopySections(state.wallets || []);
    });
  });

  document.querySelectorAll('[data-vault-builder-back]').forEach(btn => {
    btn.addEventListener('click', () => {
      state.vaultBuilderStep = 0;
      renderCopySections(state.wallets || []);
    });
  });

  document.querySelectorAll('[data-create-inline-vault]').forEach(btn => {
    btn.addEventListener('click', () => createInlineVaultFromBuilder(btn));
  });
}

async function createInlineVaultFromBuilder(btn) {
  if (state.isCreatingCopy) return;

  const selected = selectedVaultTraderAddresses();
  if (selected.length < 3) {
    alert('Add at least 3 valid trader wallets.');
    return;
  }
  if (selected.length > 10) {
    alert('Maximum 10 traders per vault.');
    return;
  }
  const effectiveVisibleVaultCount = multiWalletCount() + (isFatBotVaultsView() && !isVaultClosed(defaultVaultWallet()) ? 1 : 0);
  if (effectiveVisibleVaultCount >= unlockedVaultSlotLimit()) {
    showMultiSlotsFullAlert();
    return;
  }

  state.isCreatingCopy = true;
  const originalText = btn ? btn.textContent : '';
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Creating vault...';
  }

  try {
    const pool = await api('/api/pools', {
      method: 'POST',
      body: JSON.stringify({
        name: state.vaultName || `FatBot Vault #${state.activeVaultBuilderSlot || 1}`,
        vault_name: state.vaultName || `FatBot Vault #${state.activeVaultBuilderSlot || 1}`,
        trader_addresses: selected,
        multiplier: state.wizardSettings.multiplier,
      }),
    });

    if (!pool || !pool.wallet_id) {
      throw new Error('Vault API created no wallet_id. Check backend /api/pools response.');
    }

    await api(`/api/wallets/${pool.wallet_id}/settings`, {
      method: 'PATCH',
      body: JSON.stringify(state.wizardSettings),
    });
    const activatedWallet = await api(`/api/wallets/${pool.wallet_id}/activate`, { method: 'POST' });

    if (activatedWallet && activatedWallet.id) {
      upsertWalletInState(activatedWallet);
    } else {
      const freshWallet = await api(`/api/wallets/${pool.wallet_id}`);
      upsertWalletInState(freshWallet);
    }

    state.activeVaultBuilderSlot = null;
    state.vaultBuilderStep = 0;
    state.selectedMultiTraders = [];
    state.vaultName = '';
    renderCopySections(state.wallets || []);
    renderMultiLeaderboard(state.pools || [], state.wallets || []);

    await loadAll();
    alert('Vault created.');
  } catch (err) {
    console.error(err);
    alert(`Create failed: ${err.message || err}`);
  } finally {
    state.isCreatingCopy = false;
    if (btn) {
      btn.disabled = false;
      btn.textContent = originalText || 'Create and fund vault address';
    }
  }
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
        if (state.selectedMultiTraders.length >= 10) {
          input.checked = false;
          alert('You can select maximum 10 wallets.');
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
    if (state.selectedMultiTraders.length >= 10) {
      alert('You can select maximum 10 wallets.');
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
  const nextBtn = document.getElementById('wizardNext');
  const originalText = nextBtn ? nextBtn.textContent : '';
  const isMulti = state.copySetupMode === 'multi';
  const isVaultSingle = state.copySetupMode === 'vault_single';

  if (isMulti && state.wizardStep === 0) {
    const selected = selectedVaultTraderAddresses();
    if (selected.length < 3) {
      alert('Add at least 3 valid trader wallets.');
      return;
    }
    if (selected.length > 10) {
      alert('Maximum 10 traders per vault.');
      return;
    }
    state.selectedMultiTraders = selected.slice(0, 10);
    state.wizardStep = 1;
    renderWizard();
    return;
  }

  if (state.isCreatingCopy) return;
  state.isCreatingCopy = true;

  if (nextBtn) {
    nextBtn.disabled = true;
    nextBtn.textContent = (isMulti && state.wizardStep === 1) ? 'Creating vault...' : 'Creating...';
  }

  try {
    if (isMulti && state.wizardStep === 1) {
      if (multiWalletCount() >= unlockedVaultSlotLimit()) {
        showMultiSlotsFullAlert();
        return;
      }
      const selected = selectedVaultTraderAddresses();
      if (selected.length < 3) {
        alert('Add at least 3 valid trader wallets.');
        return;
      }
      if (selected.length > 10) {
        alert('Maximum 10 traders per vault.');
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

    if (state.wizardStep === 0) {
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
          : (state.copySetupMode === 'multi' ? 'Create and fund vault address' : 'Create and fund copytrading wallet')
      );
    }
  }
}

function backWizard() {
  state.wizardStep = Math.max(0, state.wizardStep - 1);
  renderWizard();
}

function openModal(id) { document.getElementById(id).classList.remove('hidden'); }
function closeModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;
  modal.classList.add('hidden');
  if (id === 'copyModal') modal.classList.remove('direct-copy-modal');
}

function bindMainNavigation() {
  document.querySelectorAll('[data-main-view]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-main-view]').forEach(x => x.classList.remove('active'));
      btn.classList.add('active');
      state.mainView = btn.dataset.mainView === 'fatbot-vaults' ? 'fatbot-vaults' : 'copytrading';
      renderTopInfoPanel();
      renderLeaderboardTabs();
      renderCopySections(state.wallets || []);
      renderMultiLeaderboard(state.pools || [], state.wallets || []);
      state.liveFeedTransactions = generateRandomFeedTransactions(50);
      renderRandomLiveFeed();
    });
  });
}

document.addEventListener('click', (e) => {
  if (e.target.dataset.close) closeModal(e.target.dataset.close);
  if (e.target && e.target.id === 'traderModal') closeModal('traderModal');
  if (e.target && e.target.id === 'copyModal') closeModal('copyModal');
});

const wizardNextBtn = document.getElementById('wizardNext');
const wizardBackBtn = document.getElementById('wizardBack');
if (wizardNextBtn) wizardNextBtn.addEventListener('click', nextWizard);
if (wizardBackBtn) wizardBackBtn.addEventListener('click', backWizard);

bindMainNavigation();
bindLeaderboardCategoryTabs();
ensureFatbotHowItWorksLoop();
renderTopInfoPanel();
readLeaderboardFiltersFromDom();
syncCategoryToMarketFilter();

loadAll().catch(err => {
  console.error(err);
  document.body.insertAdjacentHTML('afterbegin', `<div style="background:#ff657f;color:white;padding:12px;text-align:center;font-weight:900">Initial load error: ${err.message}</div>`);
});


function renderTargets() { /* removed in v9 */ }


/* v112 verified: openTrader is async */

/* v113 verified: loading state no longer references trader before API response */

/* v114 profile layout cleanup */

/* v115 profile stats 3x3 with account age restored */

/* v116 leaderboard: rank removed, volume/gross exposure added */

/* v117 leaderboard: sparkline default 50, gross exposure backend enrichment */

/* v118 backend profile chart restore cache-bust */

/* v119 leaderboard column order: pnl-value-volume-exposure-winrate-chart */

/* v120 leaderboard categories: tradfi, crypto, bull, bears, fatbot selection, favourite */

/* v121 category runtime fix */

/* v122 fixed categories: filter bar removed */

/* v123 category runtime fully restored */

/* v124 speed caps + profile chart fallback from mini sparkline */

/* v125: Top Trades category + TradFi threshold 70% */

/* v126 server-side precomputed leaderboard snapshots; charts preserved */

/* v127 FatBot Selection addresses + hide no-open-position wallets */

/* v128 snapshot chart enrichment: never remove mini/profile charts */

/* v129 FatBot Selection uses direct real wallet scan */

/* v130 FatBot Selection public HL direct scan + snapshot profile lookup */

/* v133 wallet aliases, Hypurrscan links, 30D labels, profile back/backdrop close */

/* v134 exact external-link SVG icon and robust Longterm profitable display */

/* v135 profile modal wallet rename + Hypurrscan redirect actions */

/* v137 redesigned direct Copy Wallet modal */

/* v138 direct copy modal starts with chart; link moved to copy source; copytrading name label */

/* v139 gross exposure multiplier wording + leaderboard tab font/border tweak */

/* v140 copy modal back arrow + backdrop close */

/* v141 FatBot Selection: 30D metrics + 6M public HL portfolio charts; hide no live positions */

/* v142 stable FatBot Selection refresh: last-good snapshot retention */

/* v144 FatBot Vault builder: 10 slots, first 3 unlocked, Add to vault, min 3/max 10 traders */

/* v145 inline FatBot Vault builder under slot with dropdown wallet selection */

/* v146 vault builder input-only trader slots */

/* v147 robust Add to vault CTA in FatBot Vaults panel */

/* v148 locked vault slots: visible unlock text and stronger blur */

/* v149 locked vault slot unlock text in one horizontal line */

/* v150 locked vault slot text made visible across full row */

/* v151 default live FatBot vault modal with stats/management tabs */

/* v152 default vault modal renders immediately and wallet management has 7 placeholder members */

/* v153 Wallet Management 30D chart previews */

/* v154 default vault uses /api/fatbot-vaults live rows and backend attaches chart data */

/* v155 fixed default vault modal render: removed undefined helpers and added safe fallback */

/* v156 vault stats 3x3 grid identical to single wallet detail cards */

/* v157 vault stats grid uses dedicated 3-column layout, not inherited detail-grid */

/* v159 all FatBot Vault rows now open the unified vault modal; vault cards use 7D mini PnL chart instead of drift */

/* v160 FatBot Vaults top-right panel swaps PnL Allocation for a looping How it Works walkthrough */

/* v161 vault cards use pulsing status dot, vault live-price formatting improved, and Wallet Management gets Close Vault flow */

/* v162 vault cards compacted into one row, closed vaults persist as hidden empty slots, and Liq formatting matches live price precision. */

/* v164 removed preset FatBot Vault #2/#3 and replaced browser prompt with styled Close Vault dialog */

/* v165 create-vault count uses visible vaults only, so hidden preset vaults do not block Start FatBot Vault. */

/* v166 deletes preset FatBot Vault #2/#3 from DB/state and fixes vault create max/min to 3-10 traders. */

/* v167 fixed create vault preview: no label-based deletion/filtering and immediate state upsert after activation. */

/* v168 Close Vault dialog uses in-app two-click confirmation, no browser confirm. */

/* v169 single copytrading rows open modal dialog; close copytrading uses same in-app withdraw confirmation flow. */

/* v170 model single copy slot from 0x0baFb25EF191bFe7A2727E14F5BbfC36610EC62A */

/* v171 model single copy slot always visible and rerenders from exact live FatBot vault data. */

/* v172 unknown coin icons resolve through backend /api/token-icon/{coin} with override/CoinGecko/CryptoCompare fallback. */
