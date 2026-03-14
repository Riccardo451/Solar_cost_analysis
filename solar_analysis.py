"""
╔══════════════════════════════════════════════════════════════════╗
║         ANALISI AMMORTAMENTO IMPIANTO FOTOVOLTAICO              ║
║                   Modello Finanziario Completo                   ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import FuncFormatter
import warnings
warnings.filterwarnings('ignore')


# ╔══════════════════════════════════════════════════════════════════╗
# ║                  ★  PARAMETRI UTENTE  ★                        ║
# ║          Modifica solo questa sezione per personalizzare        ║
# ╚══════════════════════════════════════════════════════════════════╝

# ── IMPIANTO ──────────────────────────────────────────────────────

POTENZA_KWP = 6.0
# Potenza installata in kilowatt-picco (kWp)

ESPOSIZIONE = 'Sud'
# Orientamento dei pannelli. Opzioni disponibili:
#   'Sud'  'Sud-Est'  'Sud-Ovest'  'Est'  'Ovest'  'Nord-Est'  'Nord-Ovest'  'Nord'

ZONA_GEOGRAFICA = 'Nord Italia (Milano/Torino)'
# Influenza le ore di sole equivalenti annue. Opzioni disponibili:
#   'Nord Italia (Milano/Torino)'   → 1200 h/anno
#   'Centro Italia (Roma/Firenze)'  → 1350 h/anno
#   'Sud Italia (Napoli/Bari)'      → 1500 h/anno
#   'Sicilia/Sardegna'              → 1600 h/anno

PERFORMANCE_RATIO = 0.80
# Efficienza reale dell'impianto (perdite: cablaggio, calore, inverter, sporco)
# Valori tipici: 0.75 (impianto vecchio) → 0.85 (impianto ottimo)

DEGRADO_ANNUO = 0.005
# Perdita di efficienza annua dei pannelli (valore composto)
# Valori tipici: 0.004 (pannelli premium) → 0.008 (pannelli entry-level)

# ── COSTI ─────────────────────────────────────────────────────────

COSTO_IMPIANTO_EUR = 11_000
# Costo totale dell'impianto fotovoltaico (pannelli + inverter + installazione)
# Indicativo 2024: ~1500-2000 €/kWp chiavi in mano

COSTO_BATTERIA_EUR = 6_000
# Costo del sistema di accumulo (batteria). Metti 0 se non presente.
# Indicativo 2024: ~500-700 €/kWh di capacità (es. 10 kWh ≈ 5000-7000 €)

COSTO_MANUTENZIONE_ANNUO_EUR = 100
# Spese annue di manutenzione (pulizia pannelli, assicurazione, piccoli interventi)

ANNO_SOSTITUZIONE_INVERTER = 13
# Anno in cui si prevede la sostituzione dell'inverter (vita media: 10-15 anni)

COSTO_SOSTITUZIONE_INVERTER_EUR = 1_400
# Costo di sostituzione dell'inverter. Lascia 0 per ignorarlo.
# Indicativo: 150-300 €/kWp

# ── ENERGIA ───────────────────────────────────────────────────────

PREZZO_ENERGIA_ACQUISTO_EUR_KWH = 0.22
# Prezzo attuale dell'energia elettrica acquistata dalla rete (€/kWh)
# In bolletta tipicamente tra 0.20 e 0.35 €/kWh (incluse tasse e oneri)

PREZZO_ENERGIA_VENDITA_EUR_KWH = 0.12
# Prezzo di vendita dell'energia immessa in rete (ritiro dedicato GSE, €/kWh)
# Tipicamente molto inferiore al prezzo di acquisto: 0.05-0.12 €/kWh

AUTOCONSUMO_PERCENTUALE = 0.70
# Quota di energia prodotta consumata direttamente in casa (0.0 - 1.0)
# Senza batteria: 0.25-0.45 tipico   |   Con batteria: 0.55-0.80

INCREMENTO_PREZZO_ENERGIA_ANNUO = 0.03
# Aumento annuo atteso del prezzo dell'energia (tasso composto)
# Storico EU ultimi 10 anni: ~3-5%. Usa 0.02 per stima prudente, 0.06 per aggressiva.

# ── INCENTIVI FISCALI ─────────────────────────────────────────────

TIPO_INCENTIVO = 'detrazione_50'
# Tipo di incentivo statale. Opzioni disponibili:
#   'detrazione_50'  → Detrazione IRPEF 50% in 10 anni (attuale regime IT)
#   'detrazione_36'  → Detrazione IRPEF 36% in 10 anni
#   'nessuno'        → Nessun incentivo

ANNI_DETRAZIONE = 10
# Numero di anni su cui spalmare la detrazione fiscale (normalmente 10)

# ── PARAMETRI FINANZIARI ──────────────────────────────────────────

TASSO_SCONTO = 0.03
# Tasso di sconto per calcolo NPV e Discounted Payback Period
# Rappresenta il costo opportunità del capitale (es. rendimento alternativo)
# Tipico: 0.02-0.04 (investimenti a basso rischio)

ANNI_ANALISI = 25
# Orizzonte temporale dell'analisi (anni). Vita utile tipica: 25-30 anni.

# ── OUTPUT ────────────────────────────────────────────────────────

CARTELLA_OUTPUT = '.'
# Cartella dove salvare i grafici PNG.
# '.'  → stessa cartella dello script (funziona su Colab, locale, ecc.)
# Esempio: '/content/drive/MyDrive/fotovoltaico' per Google Drive

# ╚══════════════════════════════════════════════════════════════════╝
#   Fine sezione parametri — non modificare il codice sottostante
# ╔══════════════════════════════════════════════════════════════════╝


# ─────────────────────────────────────────────────────────────────
# TABELLE DI RIFERIMENTO (non modificare)
# ─────────────────────────────────────────────────────────────────

FATTORI_ESPOSIZIONE = {
    'Sud':          1.00,
    'Sud-Est':      0.97,
    'Sud-Ovest':    0.97,
    'Est':          0.74,
    'Ovest':        0.74,
    'Nord-Est':     0.50,
    'Nord-Ovest':   0.50,
    'Nord':         0.40,
}

ORE_PICCO_ZONA = {
    'Nord Italia (Milano/Torino)':   1200,
    'Centro Italia (Roma/Firenze)':  1350,
    'Sud Italia (Napoli/Bari)':      1500,
    'Sicilia/Sardegna':              1600,
}

# ─────────────────────────────────────────────────────────────────
# COSTRUZIONE SCENARIO DAI PARAMETRI UTENTE
# ─────────────────────────────────────────────────────────────────

SCENARIO_BASE = {
    'potenza_kwp':                    POTENZA_KWP,
    'esposizione':                    ESPOSIZIONE,
    'ore_picco':                      ORE_PICCO_ZONA[ZONA_GEOGRAFICA],
    'performance_ratio':              PERFORMANCE_RATIO,
    'degrado_annuo':                  DEGRADO_ANNUO,
    'costo_impianto':                 COSTO_IMPIANTO_EUR,
    'costo_batteria':                 COSTO_BATTERIA_EUR,
    'costo_manutenzione_annuo':       COSTO_MANUTENZIONE_ANNUO_EUR,
    'anno_sostituzione_inverter':     ANNO_SOSTITUZIONE_INVERTER,
    'costo_sostituzione_inverter':    COSTO_SOSTITUZIONE_INVERTER_EUR,
    'prezzo_energia_acquisto':        PREZZO_ENERGIA_ACQUISTO_EUR_KWH,
    'prezzo_energia_vendita':         PREZZO_ENERGIA_VENDITA_EUR_KWH,
    'autoconsumo_pct':                AUTOCONSUMO_PERCENTUALE,
    'incremento_prezzo_energia':      INCREMENTO_PREZZO_ENERGIA_ANNUO,
    'tipo_incentivo':                 TIPO_INCENTIVO,
    'anni_detrazione':                ANNI_DETRAZIONE,
    'tasso_sconto':                   TASSO_SCONTO,
    'anni_analisi':                   ANNI_ANALISI,
}

# ─────────────────────────────────────────────────────────────────
# CONFIGURAZIONE GRAFICA
# ─────────────────────────────────────────────────────────────────

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.titleweight': 'bold',
    'axes.labelsize': 10,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.facecolor': '#0f1117',
    'axes.facecolor': '#1a1d27',
    'axes.labelcolor': '#c8d0e0',
    'axes.titlecolor': '#e8ecf4',
    'xtick.color': '#8890a4',
    'ytick.color': '#8890a4',
    'grid.color': '#2a2d3a',
    'grid.linewidth': 0.7,
    'text.color': '#c8d0e0',
    'legend.facecolor': '#1a1d27',
    'legend.edgecolor': '#2a2d3a',
    'legend.labelcolor': '#c8d0e0',
})

COLORS = {
    'gold':    '#f5c542',
    'green':   '#4ade80',
    'blue':    '#60a5fa',
    'orange':  '#fb923c',
    'red':     '#f87171',
    'purple':  '#c084fc',
    'teal':    '#2dd4bf',
    'gray':    '#6b7280',
    'bg':      '#0f1117',
    'panel':   '#1a1d27',
    'border':  '#2a2d3a',
    'text':    '#c8d0e0',
    'accent':  '#e8ecf4',
}

# ─────────────────────────────────────────────────────────────────
# MODELLO FINANZIARIO
# ─────────────────────────────────────────────────────────────────

def calcola_produzione_annua(potenza_kwp, ore_picco, esposizione,
                              performance_ratio, anno, degrado_annuo):
    fattore_esp = FATTORI_ESPOSIZIONE[esposizione]
    fattore_degrado = (1 - degrado_annuo) ** anno
    return potenza_kwp * ore_picco * fattore_esp * performance_ratio * fattore_degrado


def calcola_risparmio_annuo(produzione_kwh, autoconsumo_pct,
                             prezzo_acquisto, prezzo_vendita):
    autoconsumata = produzione_kwh * autoconsumo_pct
    immessa = produzione_kwh * (1 - autoconsumo_pct)
    return {
        'energia_autoconsumata_kwh': autoconsumata,
        'energia_immessa_kwh': immessa,
        'risparmio_autoconsumo_eur': autoconsumata * prezzo_acquisto,
        'ricavo_immissione_eur': immessa * prezzo_vendita,
        'totale_beneficio_eur': autoconsumata * prezzo_acquisto + immessa * prezzo_vendita,
    }


def calcola_incentivi_annui(costo_impianto, anno, tipo_incentivo, anni_detrazione):
    if tipo_incentivo == 'nessuno':
        return 0.0
    aliquota = 0.50 if tipo_incentivo == 'detrazione_50' else 0.36
    if 0 < anno <= anni_detrazione:
        return costo_impianto * aliquota / anni_detrazione
    return 0.0


def _calcola_irr(flussi, guess=0.1, max_iter=1000):
    r = guess
    for _ in range(max_iter):
        npv  = sum(f / (1 + r) ** i for i, f in enumerate(flussi))
        dnpv = sum(-i * f / (1 + r) ** (i + 1) for i, f in enumerate(flussi))
        if abs(dnpv) < 1e-10:
            break
        r_new = r - npv / dnpv
        if abs(r_new - r) < 1e-8:
            return r_new
        r = r_new
    return r


def analisi_completa(params):
    anni      = params['anni_analisi']
    costo_tot = params['costo_impianto'] + params.get('costo_batteria', 0)
    anni_arr  = np.arange(1, anni + 1)

    produzioni, benefici_lordi, incentivi = [], [], []
    costi_op_list, flussi_netti, flussi_cum = [], [], []
    prezzi_energia = []

    cumulato = -costo_tot

    for anno in anni_arr:
        prezzo_acq  = params['prezzo_energia_acquisto']  * (1 + params['incremento_prezzo_energia']) ** (anno - 1)
        prezzo_vend = params['prezzo_energia_vendita']   * (1 + params['incremento_prezzo_energia']) ** (anno - 1)
        prezzi_energia.append(prezzo_acq)

        prod = calcola_produzione_annua(
            params['potenza_kwp'], params['ore_picco'], params['esposizione'],
            params['performance_ratio'], anno - 1, params['degrado_annuo'])
        produzioni.append(prod)

        ris      = calcola_risparmio_annuo(prod, params['autoconsumo_pct'], prezzo_acq, prezzo_vend)
        beneficio = ris['totale_beneficio_eur']
        benefici_lordi.append(beneficio)

        incentivo = calcola_incentivi_annui(
            params['costo_impianto'], anno,
            params['tipo_incentivo'], params.get('anni_detrazione', 10))
        incentivi.append(incentivo)

        costo_op = params['costo_manutenzione_annuo']
        if anno == params.get('anno_sostituzione_inverter', 13):
            costo_op += params.get('costo_sostituzione_inverter', 0)
        costi_op_list.append(costo_op)

        flusso = beneficio + incentivo - costo_op
        flussi_netti.append(flusso)
        cumulato += flusso
        flussi_cum.append(cumulato)

    # Payback semplice
    payback = None
    for i, cum in enumerate(flussi_cum):
        if cum >= 0:
            payback = anni_arr[i] if i == 0 else anni_arr[i-1] + (-flussi_cum[i-1]) / (cum - flussi_cum[i-1])
            break

    # NPV
    ts   = params.get('tasso_sconto', 0.03)
    npv  = -costo_tot + sum(f / (1 + ts) ** (i + 1) for i, f in enumerate(flussi_netti))

    # IRR
    try:
        irr = _calcola_irr([-costo_tot] + flussi_netti)
    except Exception:
        irr = None

    # Discounted Payback
    dpp, cum_att = None, -costo_tot
    for i, f in enumerate(flussi_netti):
        cum_att += f / (1 + ts) ** (i + 1)
        if cum_att >= 0 and dpp is None:
            dpp = anni_arr[i]

    roi          = (sum(b + inc - co for b, inc, co in zip(benefici_lordi, incentivi, costi_op_list)) - costo_tot) / costo_tot * 100
    energia_tot  = sum(produzioni)
    co2          = energia_tot * 0.233 / 1000

    return {
        'anni': anni_arr,
        'produzioni':      np.array(produzioni),
        'benefici_lordi':  np.array(benefici_lordi),
        'incentivi':       np.array(incentivi),
        'costi_operativi': np.array(costi_op_list),
        'flussi_netti':    np.array(flussi_netti),
        'flussi_cumulati': np.array(flussi_cum),
        'prezzi_energia':  np.array(prezzi_energia),
        'payback': payback, 'npv': npv, 'irr': irr,
        'dpp': dpp, 'roi': roi,
        'energia_totale': energia_tot, 'co2_risparmiata': co2,
        'costo_totale': costo_tot,
    }


# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────

def fmt_eur(x, pos=None):
    return f"€{x/1000:.1f}k" if abs(x) >= 1000 else f"€{x:.0f}"

def out_path(filename):
    """Restituisce il percorso di output compatibile con qualsiasi ambiente."""
    os.makedirs(CARTELLA_OUTPUT, exist_ok=True)
    return os.path.join(CARTELLA_OUTPUT, filename)


# ─────────────────────────────────────────────────────────────────
# GRAFICI
# ─────────────────────────────────────────────────────────────────

def plot_analisi_completa(params=None, titolo_scenario="Scenario Base"):
    if params is None:
        params = SCENARIO_BASE.copy()
    r = analisi_completa(params)

    fig = plt.figure(figsize=(20, 14))
    fig.patch.set_facecolor(COLORS['bg'])

    fig.text(0.5, 0.97, '☀  ANALISI AMMORTAMENTO IMPIANTO FOTOVOLTAICO',
             ha='center', va='top', fontsize=18, fontweight='bold',
             color=COLORS['gold'], family='monospace')
    fig.text(0.5, 0.94,
             f'{titolo_scenario}  ·  {params["potenza_kwp"]} kWp  ·  '
             f'Esposizione {params["esposizione"]}  ·  {params["anni_analisi"]} anni',
             ha='center', va='top', fontsize=11, color=COLORS['text'])

    gs   = GridSpec(3, 4, figure=fig, top=0.91, bottom=0.06, hspace=0.45, wspace=0.35)
    anni = r['anni']

    # ── Flusso cumulato ──────────────────────────────────────────
    ax = fig.add_subplot(gs[0, 0:2])
    cum = r['flussi_cumulati']
    ax.fill_between(anni, cum, 0, where=(cum >= 0), alpha=0.25, color=COLORS['green'])
    ax.fill_between(anni, cum, 0, where=(cum <  0), alpha=0.25, color=COLORS['red'])
    ax.plot(anni, cum, color=COLORS['gold'], lw=2.5, zorder=5)
    ax.axhline(0, color=COLORS['border'], lw=1.5, ls='--')
    if r['payback']:
        ax.axvline(r['payback'], color=COLORS['green'], lw=1.8, ls=':', alpha=0.9)
        ax.text(r['payback'] + 0.3, ax.get_ylim()[0] * 0.7,
                f"Break-even\n{r['payback']:.1f} anni",
                color=COLORS['green'], fontsize=8.5, va='bottom')
    ax.annotate(f"NPV = {fmt_eur(r['npv'])}",
                xy=(anni[-1], cum[-1]), xytext=(anni[-1] - 4, cum[-1] * 0.85),
                color=COLORS['gold'], fontsize=9,
                arrowprops=dict(arrowstyle='->', color=COLORS['gold'], lw=1.2))
    ax.set_title('Flusso di Cassa Cumulato', color=COLORS['accent'])
    ax.set_xlabel('Anno'); ax.set_ylabel('€')
    ax.yaxis.set_major_formatter(FuncFormatter(fmt_eur))
    ax.grid(True, alpha=0.4)

    # ── Composizione benefici annui ───────────────────────────────
    ax = fig.add_subplot(gs[0, 2:4])
    ax.bar(anni, r['benefici_lordi'],  0.7, label='Risparmio/Ricavo energia', color=COLORS['blue'],   alpha=0.85)
    ax.bar(anni, r['incentivi'],       0.7, bottom=r['benefici_lordi'],        label='Incentivi fiscali', color=COLORS['gold'],   alpha=0.85)
    ax.bar(anni, -r['costi_operativi'],0.7, label='Costi operativi',            color=COLORS['red'],    alpha=0.70)
    ax.axhline(0, color=COLORS['border'], lw=1)
    ax.set_title('Composizione Benefici Annui', color=COLORS['accent'])
    ax.set_xlabel('Anno'); ax.set_ylabel('€/anno')
    ax.yaxis.set_major_formatter(FuncFormatter(fmt_eur))
    ax.legend(fontsize=8, loc='upper right')
    ax.grid(True, alpha=0.3, axis='y')

    # ── Produzione con degrado ────────────────────────────────────
    ax = fig.add_subplot(gs[1, 0:2])
    colori_g = plt.cm.YlOrRd_r(np.linspace(0.2, 0.8, len(anni)))
    ax.bar(anni, r['produzioni'], color=colori_g, alpha=0.9, width=0.8)
    ax.plot(anni, r['produzioni'], color=COLORS['gold'], lw=1.5, ls='--', alpha=0.7, label='Trend degrado')
    p0, pf = r['produzioni'][0], r['produzioni'][-1]
    ax.annotate(f"{pf:.0f} kWh\n(-{(1-pf/p0)*100:.1f}%)",
                xy=(anni[-1], pf), xytext=(anni[-1]-6, pf+200),
                color=COLORS['orange'], fontsize=8,
                arrowprops=dict(arrowstyle='->', color=COLORS['orange'], lw=1))
    ax.set_title('Produzione Annua con Degrado', color=COLORS['accent'])
    ax.set_xlabel('Anno'); ax.set_ylabel('kWh/anno')
    ax.grid(True, alpha=0.3, axis='y'); ax.legend(fontsize=8)

    # ── Evoluzione prezzi energia ─────────────────────────────────
    ax  = fig.add_subplot(gs[1, 2:4])
    ax.plot(anni, r['prezzi_energia'], color=COLORS['orange'], lw=2, label='Prezzo acquisto €/kWh')
    ax2 = ax.twinx()
    ax2.plot(anni, r['benefici_lordi'] / r['produzioni'],
             color=COLORS['teal'], lw=2, ls='--', label='Valore medio prod. €/kWh')
    ax2.tick_params(colors=COLORS['text'])
    ax2.set_ylabel('€/kWh (valore prod.)', color=COLORS['teal'])
    ax2.spines['right'].set_color(COLORS['border'])
    ax2.spines['top'].set_visible(False)
    ax2.yaxis.label.set_color(COLORS['teal'])
    ax.set_title('Evoluzione Prezzi Energia', color=COLORS['accent'])
    ax.set_xlabel('Anno'); ax.set_ylabel('€/kWh (acquisto)', color=COLORS['orange'])
    ax.grid(True, alpha=0.3)
    lines1, l1 = ax.get_legend_handles_labels()
    lines2, l2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, l1 + l2, fontsize=8)

    # ── Payback per esposizione ───────────────────────────────────
    ax = fig.add_subplot(gs[2, 0:2])
    esposizioni = ['Nord', 'Est', 'Ovest', 'Sud-Ovest', 'Sud-Est', 'Sud']
    pbs = []
    for esp in esposizioni:
        p = params.copy(); p['esposizione'] = esp
        re = analisi_completa(p)
        pbs.append(re['payback'] if re['payback'] else 30)
    x = np.arange(len(esposizioni))
    bar_colors = [COLORS['red'], COLORS['orange'], COLORS['orange'],
                  COLORS['blue'], COLORS['blue'], COLORS['green']]
    bars = ax.bar(x, pbs, color=bar_colors, alpha=0.85, width=0.6)
    if params['esposizione'] in esposizioni:
        idx = esposizioni.index(params['esposizione'])
        bars[idx].set_edgecolor(COLORS['gold']); bars[idx].set_linewidth(2.5)
    ax.set_xticks(x); ax.set_xticklabels(esposizioni, fontsize=9)
    ax.set_title('Payback Period per Esposizione', color=COLORS['accent'])
    ax.set_ylabel('Anni')
    ax.axhline(10, color=COLORS['green'],  ls=':', lw=1, alpha=0.6, label='10 anni')
    ax.axhline(15, color=COLORS['orange'], ls=':', lw=1, alpha=0.6, label='15 anni')
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3, axis='y')
    for bar, pb in zip(bars, pbs):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f"{pb:.1f}a" if pb < 30 else ">25a",
                ha='center', va='bottom', fontsize=8, color=COLORS['accent'])

    # ── Sensitività prezzo energia ────────────────────────────────
    ax = fig.add_subplot(gs[2, 2:4])
    incrementi = np.linspace(-0.02, 0.08, 50)
    pbs_s, npvs_s = [], []
    for inc in incrementi:
        p = params.copy(); p['incremento_prezzo_energia'] = inc
        rs = analisi_completa(p)
        pbs_s.append(rs['payback'] if rs['payback'] else 30)
        npvs_s.append(rs['npv'])
    ax.plot(incrementi * 100, pbs_s, color=COLORS['blue'], lw=2, label='Payback (anni)')
    ax2 = ax.twinx()
    ax2.plot(incrementi * 100, [n/1000 for n in npvs_s],
             color=COLORS['green'], lw=2, ls='--', label='NPV (k€)')
    ax2.tick_params(colors=COLORS['text'])
    ax2.spines['right'].set_color(COLORS['border'])
    ax2.spines['top'].set_visible(False)
    ax2.set_ylabel('NPV (k€)', color=COLORS['green'])
    ax2.yaxis.label.set_color(COLORS['green'])
    ax.axvline(params['incremento_prezzo_energia'] * 100,
               color=COLORS['gold'], ls=':', lw=1.5, label='Scenario attuale')
    ax.set_title('Sensitività: Incremento Prezzo Energia', color=COLORS['accent'])
    ax.set_xlabel('Incremento annuo prezzo energia (%)')
    ax.set_ylabel('Payback (anni)', color=COLORS['blue'])
    ax.grid(True, alpha=0.3)
    lines1, l1 = ax.get_legend_handles_labels()
    lines2, l2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, l1 + l2, fontsize=8)

    # ── KPI box ───────────────────────────────────────────────────
    kpi = [
        ("⏱  Payback",       f"{r['payback']:.1f} anni" if r['payback'] else ">25 anni",  COLORS['gold']),
        ("📊  NPV",           fmt_eur(r['npv']),  COLORS['green'] if r['npv'] > 0 else COLORS['red']),
        ("📈  IRR",           f"{r['irr']*100:.1f}%" if r['irr'] else "N/A",              COLORS['teal']),
        ("🔖  ROI 25a",       f"{r['roi']:.0f}%",                                         COLORS['blue']),
        ("⚡  Energia tot.",  f"{r['energia_totale']/1000:.1f} MWh",                       COLORS['orange']),
        ("🌱  CO₂ rispark.",  f"{r['co2_risparmiata']:.1f} t",                             COLORS['green']),
    ]
    for (label, valore, col), xpos in zip(kpi, [0.085, 0.255, 0.425, 0.595, 0.765, 0.935]):
        rect = mpatches.FancyBboxPatch(
            (xpos - 0.075, - 0.030), 0.145, 0.030,
            boxstyle="round,pad=0.005", transform=fig.transFigure,
            facecolor=COLORS['panel'], edgecolor=col, linewidth=1.5, zorder=10)
        fig.add_artist(rect)
        fig.text(xpos, 0.018, label,  ha='center', va='center', fontsize=8,  color=COLORS['text'],   zorder=11)
        fig.text(xpos, - 0.015, valore, ha='center', va='center', fontsize=11, color=col, fontweight='bold', zorder=11)

    fpath = out_path('solar_analysis_dashboard.png')
    plt.savefig(fpath, dpi=160, bbox_inches='tight',
                facecolor=COLORS['bg'], edgecolor='none')
    plt.close()
    print(f"✅ Dashboard salvato: {fpath}")
    return r


def plot_confronto_scenari(params_base=None):
    if params_base is None:
        params_base = SCENARIO_BASE.copy()

    scenari = {
        'Ottimistico\n(Sud, 8% ↑ energia)': {
            **params_base, 'esposizione': 'Sud',
            'incremento_prezzo_energia': 0.08, 'autoconsumo_pct': 0.55},
        'Base\n(parametri inseriti)': params_base,
        'Con Batteria\n(+ 5k€, 70% auto)': {
            **params_base, 'costo_batteria': 5000, 'autoconsumo_pct': 0.70},
        'Pessimistico\n(Est, 1% ↑ energia)': {
            **params_base, 'esposizione': 'Est',
            'incremento_prezzo_energia': 0.01, 'autoconsumo_pct': 0.30},
    }
    colori_sc = [COLORS['green'], COLORS['gold'], COLORS['purple'], COLORS['red']]

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    fig.patch.set_facecolor(COLORS['bg'])

    # Flussi cumulati
    ax.set_facecolor(COLORS['panel'])
    ax.axhline(0, color=COLORS['border'], lw=1.5, ls='--')
    for (nome, params), col in zip(scenari.items(), colori_sc):
        r = analisi_completa(params)
        ax.plot(r['anni'], r['flussi_cumulati'], color=col, lw=2.2, label=nome)
        if r['payback']:
            ax.axvline(r['payback'], color=col, lw=0.8, ls=':', alpha=0.5)
    ax.set_title('Flusso di Cassa Cumulato — Confronto Scenari',
                 color=COLORS['accent'], fontsize=12, fontweight='bold')
    ax.set_xlabel('Anno'); ax.set_ylabel('€')
    ax.yaxis.set_major_formatter(FuncFormatter(fmt_eur))
    ax.legend(fontsize=9, loc='upper left')
    ax.grid(True, alpha=0.35)
    ax.spines[['top', 'right']].set_visible(False)

    # KPI bar
    ax2.set_facecolor(COLORS['panel'])
    nomi   = [n.split('\n')[0] for n in scenari.keys()]
    pbs, npvs = [], []
    for params in scenari.values():
        r = analisi_completa(params)
        pbs.append(r['payback'] if r['payback'] else 28)
        npvs.append(r['npv'] / 1000)

    x, w = np.arange(len(nomi)), 0.35
    bars1 = ax2.bar(x - w/2, pbs,  w, color=colori_sc, alpha=0.75)
    ax3   = ax2.twinx()
    bars2 = ax3.bar(x + w/2, npvs, w, color=colori_sc, alpha=0.45,
                    hatch='//', edgecolor=colori_sc)
    ax3.axhline(0, color=COLORS['border'], lw=1)
    ax3.set_ylabel('NPV 25 anni (k€)', color=COLORS['text'])
    ax3.tick_params(colors=COLORS['text'])
    ax3.spines[['top', 'right']].set_color(COLORS['border'])
    for bar, val in zip(bars1, pbs):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                 f"{val:.1f}a" if val < 28 else ">25a",
                 ha='center', va='bottom', fontsize=9, color=COLORS['accent'])
    for bar, val in zip(bars2, npvs):
        ax3.text(bar.get_x() + bar.get_width()/2, max(val, 0) + 0.3,
                 f"{val:.1f}k", ha='center', va='bottom', fontsize=9, color=COLORS['accent'])
    ax2.set_title('KPI per Scenario', color=COLORS['accent'], fontsize=12, fontweight='bold')
    ax2.set_xticks(x); ax2.set_xticklabels(nomi, fontsize=9)
    ax2.set_ylabel('Payback Period (anni)', color=COLORS['text'])
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.spines[['top', 'right']].set_visible(False)
    legend_els = [mpatches.Patch(facecolor=COLORS['gray'], alpha=0.75, label='Payback (anni)'),
                  mpatches.Patch(facecolor=COLORS['gray'], alpha=0.45, hatch='//', label='NPV 25a (k€)')]
    ax2.legend(handles=legend_els, fontsize=9, loc='upper right')

    fig.suptitle(f'☀  Confronto Scenari Impianto Fotovoltaico {POTENZA_KWP} kWp',
                 fontsize=14, fontweight='bold', color=COLORS['gold'], y=1.02)
    plt.tight_layout()

    fpath = out_path('solar_confronto_scenari.png')
    plt.savefig(fpath, dpi=160, bbox_inches='tight',
                facecolor=COLORS['bg'], edgecolor='none')
    plt.close()
    print(f"✅ Confronto scenari salvato: {fpath}")


# ─────────────────────────────────────────────────────────────────
# REPORT TESTUALE
# ─────────────────────────────────────────────────────────────────

def stampa_report_testuale(params=None, titolo="SCENARIO BASE"):
    if params is None:
        params = SCENARIO_BASE.copy()
    r   = analisi_completa(params)
    sep = "─" * 60

    print(f"\n{'═'*60}")
    print(f"  REPORT ANALISI FOTOVOLTAICO — {titolo}")
    print(f"{'═'*60}")
    print(f"\nPARAMETRI IMPIANTO\n{sep}")
    print(f"  Potenza installata:         {params['potenza_kwp']} kWp")
    print(f"  Esposizione:                {params['esposizione']}")
    print(f"  Ore picco equiv. (zona):    {params['ore_picco']} h/anno")
    print(f"  Performance Ratio:          {params['performance_ratio']*100:.0f}%")
    print(f"  Degrado annuo:              {params['degrado_annuo']*100:.1f}%/anno")
    print(f"  Produzione anno 1:          {r['produzioni'][0]:.0f} kWh")
    print(f"  Produzione anno {params['anni_analisi']}:         {r['produzioni'][-1]:.0f} kWh  "
          f"(-{(1-r['produzioni'][-1]/r['produzioni'][0])*100:.1f}% dal primo anno)")
    print(f"\nINVESTIMENTO\n{sep}")
    print(f"  Costo impianto:             €{params['costo_impianto']:,.0f}")
    print(f"  Costo batteria:             €{params.get('costo_batteria',0):,.0f}")
    print(f"  Costo totale:               €{r['costo_totale']:,.0f}")
    print(f"  Manutenzione annua:         €{params['costo_manutenzione_annuo']:,.0f}")
    print(f"\nPARAMETRI ECONOMICI\n{sep}")
    print(f"  Prezzo acquisto energia:    €{params['prezzo_energia_acquisto']:.3f}/kWh")
    print(f"  Prezzo vendita (GSE):       €{params['prezzo_energia_vendita']:.3f}/kWh")
    print(f"  Autoconsumo:                {params['autoconsumo_pct']*100:.0f}%")
    print(f"  Incremento prezzo/anno:     {params['incremento_prezzo_energia']*100:.1f}%")
    print(f"  Incentivo:                  {params['tipo_incentivo'].replace('_',' ').title()}")
    print(f"\nRISULTATI FINANZIARI\n{sep}")
    pb_str  = f"{r['payback']:.1f} anni" if r['payback'] else f"> {params['anni_analisi']} anni"
    dpp_str = f"{r['dpp']:.0f} anni"     if r['dpp']     else f"> {params['anni_analisi']} anni"
    irr_str = f"{r['irr']*100:.2f}%"     if r['irr']     else "N/D"
    print(f"  ⏱  Payback Period:           {pb_str}")
    print(f"  ⏱  Discounted Payback:       {dpp_str}")
    print(f"  📊  NPV ({params['anni_analisi']} anni):            €{r['npv']:,.0f}")
    print(f"  📈  IRR:                      {irr_str}")
    print(f"  🔖  ROI totale:               {r['roi']:.1f}%")
    print(f"\nIMPATTO AMBIENTALE\n{sep}")
    print(f"  ⚡  Energia prodotta:         {r['energia_totale']/1000:.1f} MWh")
    print(f"  🌱  CO₂ risparmiata:          {r['co2_risparmiata']:.1f} tonnellate")
    print(f"  🌳  Equiv. alberi piantati:   ~{r['co2_risparmiata']*50:.0f}")
    print(f"\nFLUSSI DI CASSA (anni chiave)\n{sep}")
    print(f"  {'Anno':>5}  {'Produz.':>10}  {'Beneficio':>10}  {'Incentivo':>10}  {'Cumulato':>12}")
    print(f"  {'─'*5}  {'─'*10}  {'─'*10}  {'─'*10}  {'─'*12}")
    milestones = {1, 5, 10, 15, 20, params['anni_analisi']}
    for i, anno in enumerate(r['anni']):
        if anno in milestones or (r['payback'] and abs(anno - r['payback']) < 0.6):
            print(f"  {anno:>5}  {r['produzioni'][i]:>8.0f}kWh"
                  f"  €{r['benefici_lordi'][i]:>8.0f}"
                  f"  €{r['incentivi'][i]:>8.0f}"
                  f"  €{r['flussi_cumulati'][i]:>10.0f}")
    print(f"\n{'═'*60}\n")


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*60)
    print("   ANALISI AMMORTAMENTO IMPIANTO FOTOVOLTAICO")
    print("   Modello Finanziario Completo — v2.0")
    print("="*60)

    # Report testuale con i parametri inseriti nella sezione utente
    stampa_report_testuale(SCENARIO_BASE,
        f"{POTENZA_KWP} kWp | {ESPOSIZIONE} | {ZONA_GEOGRAFICA}")

    # Dashboard grafico principale
    print("📊 Generazione dashboard principale...")
    plot_analisi_completa(SCENARIO_BASE,
        f"{POTENZA_KWP} kWp | {ZONA_GEOGRAFICA} | Esposizione {ESPOSIZIONE}")

    # Confronto scenari (ottimistico / base / batteria / pessimistico)
    print("📊 Generazione confronto scenari...")
    plot_confronto_scenari(SCENARIO_BASE)

    print(f"\n✅ Analisi completata! Grafici salvati in: '{os.path.abspath(CARTELLA_OUTPUT)}'")
