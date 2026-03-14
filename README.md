# ☀️ Analisi Ammortamento Impianto Fotovoltaico

Uno script Python per analizzare il tempo di ammortamento di un impianto solare domestico, con modello finanziario completo e grafici interattivi.

![Python](https://img.shields.io/badge/Python-3.6%2B-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Dependencies](https://img.shields.io/badge/dependencies-numpy%20%7C%20matplotlib-orange)

---

## 📋 Indice

- [Caratteristiche](#-caratteristiche)
- [Esempi di output](#-esempi-di-output)
- [Installazione](#-installazione)
- [Utilizzo](#-utilizzo)
- [Parametri](#-parametri)
- [Modello matematico](#-modello-matematico)
- [Metriche calcolate](#-metriche-calcolate)
- [Struttura del codice](#-struttura-del-codice)

---

## ✨ Caratteristiche

- **Produzione realistica** — calcola la produzione annua tenendo conto di esposizione, Performance Ratio e degrado composto dei pannelli nel tempo
- **Doppio flusso economico** — distingue energia autoconsumata (valorizzata al prezzo di acquisto) da energia immessa in rete (tariffa GSE), evitando stime sovrastimate
- **Costi nascosti inclusi** — modella la sostituzione dell'inverter (tipicamente dopo 10–15 anni) e i costi di manutenzione annuali
- **Incentivi fiscali** — supporta la detrazione IRPEF al 50% o 36% ripartita in 10 anni
- **Analisi finanziaria completa** — calcola Payback Period, NPV, IRR, Discounted Payback e ROI
- **6 grafici automatici** — dashboard principale + confronto tra 4 scenari
- **Compatibile con Google Colab** — salva i file nella directory corrente, senza dipendenze da percorsi di sistema

---

## 📊 Esempi di output

Lo script genera due file PNG nella cartella di output configurata.

### Dashboard principale
Mostra flusso di cassa cumulato con break-even visivo, composizione dei benefici annui, produzione con degrado e sensitività al prezzo dell'energia.

### Confronto scenari
Confronta quattro scenari — Ottimistico, Base, Con Batteria e Pessimistico — su payback period e NPV.

---

## 🔧 Installazione

### Prerequisiti

- Python 3.6 o superiore
- pip

### Installazione delle dipendenze

```bash
pip install numpy matplotlib
```

Su Google Colab le librerie sono già disponibili, non serve nessuna installazione.

### Download dello script

```bash
git clone https://github.com/tuo-username/analisi-fotovoltaico.git
cd analisi-fotovoltaico
```

---

## 🚀 Utilizzo

### Esecuzione base

```bash
python solar_analysis.py
```

Lo script stampa un report testuale nel terminale e salva i due grafici PNG nella cartella configurata (default: stessa cartella dello script).

### Su Google Colab

```python
# Carica il file su Colab, poi esegui:
exec(open('solar_analysis.py').read())
```

Per salvare i grafici su Google Drive, modifica il parametro `CARTELLA_OUTPUT` (vedi sezione Parametri).


## ⚙️ Parametri

Tutti i parametri si trovano nella sezione `★ PARAMETRI UTENTE ★` in cima allo script. È l'unica sezione da modificare.

### Impianto

| Parametro | Default | Descrizione |
|---|---|---|
| `POTENZA_KWP` | `6.0` | Potenza installata in kWp |
| `ESPOSIZIONE` | `'Sud'` | Orientamento pannelli (vedi tabella sotto) |
| `ZONA_GEOGRAFICA` | `'Centro Italia'` | Influenza le ore di sole equivalenti |
| `PERFORMANCE_RATIO` | `0.80` | Efficienza reale impianto (0.75–0.85) |
| `DEGRADO_ANNUO` | `0.005` | Perdita efficienza annua composta |

**Fattori di esposizione disponibili:**

| Esposizione | Fattore | Produzione relativa |
|---|---|---|
| Sud | 1.00 | 100% |
| Sud-Est / Sud-Ovest | 0.97 | 97% |
| Est / Ovest | 0.74 | 74% |
| Nord-Est / Nord-Ovest | 0.50 | 50% |
| Nord | 0.40 | 40% |

**Zone geografiche disponibili:**

| Zona | Ore picco/anno |
|---|---|
| Nord Italia (Milano/Torino) | 1150 h |
| Centro Italia (Roma/Firenze) | 1350 h |
| Sud Italia (Napoli/Bari) | 1500 h |
| Sicilia/Sardegna | 1600 h |

### Costi

| Parametro | Default | Descrizione |
|---|---|---|
| `COSTO_IMPIANTO_EUR` | `10_200` | Costo totale chiavi in mano |
| `COSTO_BATTERIA_EUR` | `0` | Costo accumulo (0 se assente) |
| `COSTO_MANUTENZIONE_ANNUO_EUR` | `120` | Manutenzione, assicurazione |
| `ANNO_SOSTITUZIONE_INVERTER` | `13` | Anno previsto sostituzione inverter |
| `COSTO_SOSTITUZIONE_INVERTER_EUR` | `1_500` | Costo sostituzione inverter |

### Energia

| Parametro | Default | Descrizione |
|---|---|---|
| `PREZZO_ENERGIA_ACQUISTO_EUR_KWH` | `0.25` | Prezzo bolletta (€/kWh) |
| `PREZZO_ENERGIA_VENDITA_EUR_KWH` | `0.08` | Tariffa GSE ritiro dedicato (€/kWh) |
| `AUTOCONSUMO_PERCENTUALE` | `0.40` | Quota produzione consumata in casa |
| `INCREMENTO_PREZZO_ENERGIA_ANNUO` | `0.03` | Aumento annuo atteso del prezzo energia |

### Incentivi e finanza

| Parametro | Default | Opzioni |
|---|---|---|
| `TIPO_INCENTIVO` | `'detrazione_50'` | `'detrazione_50'`, `'detrazione_36'`, `'nessuno'` |
| `ANNI_DETRAZIONE` | `10` | Anni di ripartizione detrazione |
| `TASSO_SCONTO` | `0.03` | Costo opportunità capitale per NPV |
| `ANNI_ANALISI` | `25` | Orizzonte temporale analisi |

### Output

| Parametro | Default | Descrizione |
|---|---|---|
| `CARTELLA_OUTPUT` | `'.'` | Cartella salvataggio PNG. Su Colab con Drive: `'/content/drive/MyDrive/cartella'` |

---

## 📐 Modello matematico

### Produzione annua

La produzione di ogni anno viene calcolata applicando il degrado composto, che si accumula sull'efficienza residua dell'anno precedente — non sull'anno iniziale:

```
Produzione(anno) = Potenza × OrePicco × FattoreEsposizione × PR × (1 − Degrado)^(anno−1)
```

### Beneficio economico annuo

L'energia prodotta viene suddivisa in due flussi con valorizzazioni diverse:

```
Beneficio = (Produzione × Autoconsumo% × PrezzoAcquisto)
          + (Produzione × (1 − Autoconsumo%) × PrezzoVendita)
```

Sia il prezzo di acquisto che quello di vendita crescono ogni anno al tasso `INCREMENTO_PREZZO_ENERGIA_ANNUO` con formula composta.

### Incentivo fiscale

```
Incentivo(anno) = (CostoImpianto × Aliquota) / AnniDetrazione    se anno ≤ AnniDetrazione
                = 0                                                altrimenti
```

### Flusso di cassa

```
FlussoCassa(anno) = Beneficio(anno) + Incentivo(anno) − CostiOperativi(anno)

FlussoNetto(anno) = FlussoCassa(anno) − CostoSostituzioneInverter   (solo nell'anno previsto)
```

### Metriche finanziarie

```
NPV = −InvestimentoIniziale + Σ [ FlussoCassa(t) / (1 + TassoSconto)^t ]

IRR → tasso r tale che NPV = 0   (calcolato con Newton-Raphson)

ROI = (BeneficioTotale − InvestimentoIniziale) / InvestimentoIniziale × 100
```

---

## 📈 Metriche calcolate

| Metrica | Descrizione |
|---|---|
| **Payback Period** | Anno esatto del break-even (interpolazione lineare) |
| **Discounted Payback** | Payback considerando il valore temporale del denaro |
| **NPV** | Valore Attuale Netto sull'orizzonte di analisi |
| **IRR** | Tasso Interno di Rendimento effettivo dell'investimento |
| **ROI** | Return on Investment totale |
| **CO₂ risparmiata** | Tonnellate di CO₂ evitate (fattore ISPRA: 0.233 kg/kWh) |

---

## 🏗️ Struttura del codice

```
solar_analysis.py
│
├── ★ PARAMETRI UTENTE ★          ← unica sezione da modificare
│
├── Tabelle di riferimento
│   ├── FATTORI_ESPOSIZIONE        dict con fattori per orientamento
│   └── ORE_PICCO_ZONA             dict con ore equivalenti per zona
│
├── SCENARIO_BASE                  dict costruito dai parametri utente
│
├── Funzioni del modello
│   ├── calcola_produzione_annua() produzione con degrado composto
│   ├── calcola_risparmio_annuo()  split autoconsumo / immissione
│   ├── calcola_incentivi_annui()  detrazione IRPEF per anno
│   ├── _calcola_irr()             Newton-Raphson per IRR
│   └── analisi_completa()         motore principale, ritorna dict con serie e KPI
│
├── Funzioni di output
│   ├── plot_analisi_completa()    dashboard 6-pannelli
│   ├── plot_confronto_scenari()   confronto 4 scenari
│   └── stampa_report_testuale()   report nel terminale
│
└── main                           esegue analisi base + grafici + report
```

---

## 📦 Dipendenze

| Libreria | Versione minima | Uso |
|---|---|---|
| `numpy` | 1.18 | Calcoli vettoriali e array |
| `matplotlib` | 3.2 | Generazione grafici |

Entrambe fanno parte della distribuzione standard di Anaconda e sono preinstallate su Google Colab.

---

## 📄 Licenza

Distribuito sotto licenza MIT. Consulta il file `LICENSE` per i dettagli.
