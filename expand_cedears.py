"""
expand_cedears.py — Amplía el universo de CEDEARs (acciones + ETFs)
===================================================================
Fusiona un snapshot del listado de CEDEARs de BYMA dentro de tus dos CSV:
    data/universe_cedears.csv   (columna: ticker)
    data/ratios_cedears.csv     (columnas: ticker,ratio)

REGLA DEL PROYECTO (no inventar datos): los ratios de abajo NO son inventados,
son una FOTO del listado oficial sincronizado con BYMA (ver SOURCE/SNAPSHOT_DATE).
Igual valen como referencia: para que la solapa "Precio" en ARS sea exacta,
validá el ratio de cada papel contra Comafi/BYMA antes de confiar (cambian por
splits y acciones corporativas). El SCREENER no usa el ratio, así que para
filtrar/rankear no es crítico; sí lo es para el precio estimado en pesos.

QUÉ HACE
  - Lee tus CSV actuales y se queda con TODO lo que ya tenés (no pisa nada:
    ni tickers ni ratios que ya cargaste y validaste).
  - Agrega los CEDEARs nuevos del snapshot que falten.
  - Traduce el CÓDIGO BYMA al SÍMBOLO de yfinance cuando difieren (BA.C->BAC,
    BRKB->BRK-B, DISN->DIS, CC->CCJ, etc.). El universo alimenta yfinance, así
    que esto es lo que evita que un papel quede "sin precio".
  - Hace backup de los CSV antes de escribir (.bak) e imprime un informe de qué
    agregó, qué símbolos corrigió y qué dejó afuera.

USO
    python expand_cedears.py            # fusiona (modo real)
    python expand_cedears.py --dry-run  # muestra el informe sin escribir
    python expand_cedears.py --include-foreign   # suma también B3/Frankfurt/LSE
    python expand_cedears.py --data-dir data     # por si tu carpeta es otra

DESPUÉS
    python portfolio_research.py update   # baja precios del universo nuevo
    python portfolio_research.py funds    # baja ratios (reanudable)
  Lo que yfinance no pueda cotizar se saltea solo y se avisa: ahí ves si quedó
  algún símbolo mal mapeado.

Fuente del snapshot: listado oficial de CEDEARs sincronizado con BYMA
(vía Rankia, "Ratios de conversión CEDEAR", tabla con últ. act. 29/05/2026).
"""

import argparse
import csv
import os
import shutil
from datetime import datetime

SOURCE = "BYMA (listado oficial de ratios CEDEAR, sincronizado vía Rankia)"
SNAPSHOT_DATE = "2026-05-29"

# -----------------------------------------------------------------------------
# CORE: CEDEARs cuyo subyacente cotiza en EE.UU. (NYSE/NASDAQ/Arca) o es un ADR
# que yfinance sí cotiza. Estos se agregan por defecto.
# Formato: (simbolo_yfinance, codigo_byma, "ratio_byma", nombre)
#   ratio_byma "A:B"  ->  ratio = A/B  (CEDEARs por 1 acción subyacente)
#   "20:1"->20 ; "1:3"->0.333 ; "692:1"->692 ; "1:13"->0.0769
# Si simbolo_yfinance != codigo_byma, es una CORRECCIÓN (se marca en el informe).
# -----------------------------------------------------------------------------
CORE = [
    ("AAL",   "AAL",   "2:1",   "American Airlines"),
    ("AAP",   "AAP",   "14:1",  "Advance Auto Parts"),
    ("AAPL",  "AAPL",  "20:1",  "Apple"),
    ("ABBV",  "ABBV",  "10:1",  "AbbVie"),
    ("ABEV",  "ABEV",  "1:3",   "Ambev (ADR)"),
    ("ABNB",  "ABNB",  "15:1",  "Airbnb"),
    ("ABT",   "ABT",   "4:1",   "Abbott Labs"),
    ("ACN",   "ACN",   "75:1",  "Accenture"),
    ("ACWI",  "ACWI",  "26:1",  "iShares MSCI ACWI ETF"),
    ("ADBE",  "ADBE",  "44:1",  "Adobe"),
    ("AGRO",  "ADGO",  "1:1",   "Adecoagro"),
    ("ADI",   "ADI",   "15:1",  "Analog Devices"),
    ("ADP",   "ADP",   "6:1",   "ADP"),
    ("AEG",   "AEG",   "1:1",   "Aegon (ADR)"),
    ("AEM",   "AEM",   "6:1",   "Agnico Eagle Mines"),
    ("AI",    "AI",    "5:1",   "C3.ai"),
    ("AIG",   "AIG",   "5:1",   "American International Group"),
    ("AKO-B", "AKO.B", "1:1",   "Embotelladora Andina"),
    ("ALAB",  "ALAB",  "44:1",  "Astera Labs"),
    ("AMAT",  "AMAT",  "5:1",   "Applied Materials"),
    ("AMD",   "AMD",   "10:1",  "AMD"),
    ("AMGN",  "AMGN",  "30:1",  "Amgen"),
    ("AMX",   "AMX",   "1:1",   "America Movil (ADR)"),
    ("AMZN",  "AMZN",  "144:1", "Amazon"),
    ("ANET",  "ANET",  "29:1",  "Arista Networks"),
    ("ANF",   "ANF",   "1:1",   "Abercrombie & Fitch"),
    ("ACH",   "AOCA",  "1:1",   "Aluminum Corp of China (ADR)"),
    ("ARCO",  "ARCO",  "1:2",   "Arcos Dorados"),
    ("ARKK",  "ARKK",  "10:1",  "ARK Innovation ETF"),
    ("ARM",   "ARM",   "27:1",  "ARM Holdings"),
    ("ASML",  "ASML",  "146:1", "ASML (ADR)"),
    ("ASR",   "ASR",   "20:1",  "Grupo Aeroportuario Sureste (ADR)"),
    ("ASTS",  "ASTS",  "15:1",  "AST SpaceMobile"),
    ("AVGO",  "AVGO",  "39:1",  "Broadcom"),
    ("AVY",   "AVY",   "18:1",  "Avery Dennison"),
    ("AXP",   "AXP",   "15:1",  "American Express"),
    ("AZN",   "AZN",   "4:1",   "AstraZeneca (ADR)"),
    ("B",     "B",     "2:1",   "Barrick Mining"),
    ("BA",    "BA",    "24:1",  "Boeing"),
    ("BAC",   "BA.C",  "41:1",  "Bank of America"),
    ("BABA",  "BABA",  "9:1",   "Alibaba (ADR)"),
    ("BAK",   "BAK",   "2:1",   "Braskem (ADR)"),
    ("BB",    "BB",    "3:1",   "BlackBerry"),
    ("BBD",   "BBD",   "1:1",   "Banco Bradesco (ADR)"),
    ("BBVA",  "BBV",   "1:1",   "BBVA (ADR)"),
    ("BCS",   "BCS",   "1:1",   "Barclays (ADR)"),
    ("BHP",   "BHP",   "2:1",   "BHP (ADR)"),
    ("BIDU",  "BIDU",  "11:1",  "Baidu (ADR)"),
    ("BIIB",  "BIB",   "13:1",  "Biogen"),
    ("BIOX",  "BIOX",  "1:1",   "Bioceres Crop Solutions"),
    ("BK",    "BK",    "2:1",   "BNY Mellon"),
    ("BKNG",  "BKNG",  "700:1", "Booking"),
    ("BKR",   "BKR",   "7:1",   "Baker Hughes"),
    ("BMNR",  "BMNR",  "8:1",   "Bitmine Immersion"),
    ("BMY",   "BMY",   "3:1",   "Bristol-Myers Squibb"),
    ("BG",    "BNG",   "5:1",   "Bunge"),
    ("BP",    "BP",    "5:1",   "BP (ADR)"),
    ("BRFS",  "BRFS",  "1:3",   "BRF (ADR)"),
    ("BRK-B", "BRKB",  "22:1",  "Berkshire Hathaway B"),
    ("BSBR",  "BSBR",  "1:1",   "Santander Brasil (ADR)"),
    ("BX",    "BX",    "30:1",  "Blackstone"),
    ("C",     "C",     "3:1",   "Citigroup"),
    ("CAAP",  "CAAP",  "1:4",   "Corporacion America Airports"),
    ("CAH",   "CAH",   "3:1",   "Cardinal Health"),
    ("CAJ",   "CAJ",   "2:1",   "Canon (ADR)"),
    ("CAR",   "CAR",   "26:1",  "Avis Budget"),
    ("CAT",   "CAT",   "20:1",  "Caterpillar"),
    ("CBD",   "CBRD",  "1:1",   "Cia Brasileira de Distribuicao (ADR)"),
    ("CCJ",   "CC",    "23:1",  "Cameco"),
    ("CCL",   "CCL",   "3:1",   "Carnival"),
    ("CDE",   "CDE",   "1:1",   "Coeur Mining"),
    ("CEG",   "CEG",   "45:1",  "Constellation Energy"),
    ("CIBR",  "CIBR",  "10:1",  "First Trust NASDAQ Cybersecurity ETF"),
    ("CL",    "CL",    "3:1",   "Colgate-Palmolive"),
    ("CLS",   "CLS",   "20:1",  "Celestica"),
    ("COIN",  "COIN",  "27:1",  "Coinbase"),
    ("COP",   "COP",   "25:1",  "ConocoPhillips"),
    ("COPX",  "COPX",  "14:1",  "Global X Copper Miners ETF"),
    ("COST",  "COST",  "48:1",  "Costco"),
    ("CRM",   "CRM",   "18:1",  "Salesforce"),
    ("CRWD",  "CRWD",  "79:1",  "CrowdStrike"),
    ("CRWV",  "CRWV",  "27:1",  "CoreWeave"),
    ("CSCO",  "CSCO",  "5:1",   "Cisco"),
    ("CVS",   "CVS",   "15:1",  "CVS Health"),
    ("CVX",   "CVX",   "16:1",  "Chevron"),
    ("CX",    "CX",    "1:1",   "Cemex (ADR)"),
    ("DAL",   "DAL",   "8:1",   "Delta Air Lines"),
    ("DD",    "DD",    "5:1",   "DuPont"),
    ("DE",    "DE",    "40:1",  "Deere"),
    ("DECK",  "DECK",  "25:1",  "Deckers Outdoor"),
    ("DEO",   "DEO",   "6:1",   "Diageo (ADR)"),
    ("DHR",   "DHR",   "54:1",  "Danaher"),
    ("DIA",   "DIA",   "20:1",  "SPDR Dow Jones Industrial ETF"),
    ("DIS",   "DISN",  "12:1",  "Walt Disney"),
    ("DOCU",  "DOCU",  "22:1",  "DocuSign"),
    ("DOW",   "DOW",   "6:1",   "Dow Inc"),
    ("DTEGY", "DTEA",  "3:1",   "Deutsche Telekom (ADR)"),
    ("E",     "E",     "4:1",   "Eni (ADR)"),
    ("EA",    "EA",    "14:1",  "Electronic Arts"),
    ("EBAY",  "EBAY",  "2:1",   "eBay"),
    ("EBR",   "EBR",   "1:4",   "Eletrobras (ADR)"),
    ("ECL",   "ECL",   "56:1",  "Ecolab"),
    ("EEM",   "EEM",   "5:1",   "iShares MSCI Emerging Markets ETF"),
    ("EFA",   "EFA",   "18:1",  "iShares MSCI EAFE ETF"),
    ("EFX",   "EFX",   "16:1",  "Equifax"),
    ("ELP",   "ELP",   "1:13",  "Copel (ADR)"),
    ("EQNR",  "EQNR",  "6:1",   "Equinor (ADR)"),
    ("ERIC",  "ERIC",  "2:1",   "Ericsson (ADR)"),
    ("ERJ",   "ERJ",   "1:1",   "Embraer (ADR)"),
    ("ESGU",  "ESGU",  "30:1",  "iShares ESG Aware MSCI USA ETF"),
    ("ETHA",  "ETHA",  "5:1",   "iShares Ethereum Trust ETF"),
    ("ETSY",  "ETSY",  "16:1",  "Etsy"),
    ("EWJ",   "EWJ",   "14:1",  "iShares MSCI Japan ETF"),
    ("EWY",   "EWY",   "50:1",  "iShares MSCI South Korea ETF"),
    ("EWZ",   "EWZ",   "2:1",   "iShares MSCI Brazil ETF"),
    ("F",     "F",     "1:1",   "Ford"),
    ("FCX",   "FCX",   "3:1",   "Freeport-McMoRan"),
    ("FDX",   "FDX",   "10:1",  "FedEx"),
    ("FI",    "FISV",  "11:1",  "Fiserv"),
    ("FMCC",  "FMCC",  "1:1",   "Freddie Mac"),
    ("FMX",   "FMX",   "6:1",   "Femsa (ADR)"),
    ("FNMA",  "FNMA",  "1:1",   "Fannie Mae"),
    ("FSLR",  "FSLR",  "18:1",  "First Solar"),
    ("FXI",   "FXI",   "5:1",   "iShares China Large-Cap ETF"),
    ("GDX",   "GDX",   "10:1",  "VanEck Gold Miners ETF"),
    ("GE",    "GE",    "8:1",   "General Electric"),
    ("GFI",   "GFI",   "1:1",   "Gold Fields (ADR)"),
    ("GGB",   "GGB",   "1:4",   "Gerdau (ADR)"),
    ("GILD",  "GILD",  "4:1",   "Gilead Sciences"),
    ("GLD",   "GLD",   "50:1",  "SPDR Gold Trust ETF"),
    ("GLNG",  "GLNG",  "10:1",  "Golar LNG"),
    ("GLOB",  "GLOB",  "18:1",  "Globant"),
    ("GLW",   "GLW",   "41:1",  "Corning"),
    ("GM",    "GM",    "6:1",   "General Motors"),
    ("GOOGL", "GOOGL", "58:1",  "Alphabet"),
    ("GPRK",  "GPRK",  "1:1",   "GeoPark"),
    ("GRMN",  "GRMN",  "3:1",   "Garmin"),
    ("GS",    "GS",    "13:1",  "Goldman Sachs"),
    ("GSK",   "GSK",   "4:1",   "GSK (ADR)"),
    ("GT",    "GT",    "2:1",   "Goodyear"),
    ("HAL",   "HAL",   "2:1",   "Halliburton"),
    ("HD",    "HD",    "32:1",  "Home Depot"),
    ("HDB",   "HDB",   "2:1",   "HDFC Bank (ADR)"),
    ("HIMS",  "HIMS",  "4:1",   "Hims & Hers Health"),
    ("HL",    "HL",    "1:1",   "Hecla Mining"),
    ("HMC",   "HMC",   "1:1",   "Honda (ADR)"),
    ("HMY",   "HMY",   "1:1",   "Harmony Gold (ADR)"),
    ("HNP",   "HNPIY", "1:1",   "Huaneng Power (ADR)"),
    ("HOG",   "HOG",   "3:1",   "Harley-Davidson"),
    ("HON",   "HON",   "8:1",   "Honeywell"),
    ("HOOD",  "HOOD",  "29:1",  "Robinhood"),
    ("HPQ",   "HPQ",   "1:1",   "HP Inc"),
    ("HSBC",  "HSBC",  "2:1",   "HSBC (ADR)"),
    ("HSY",   "HSY",   "21:1",  "Hershey"),
    ("HUT",   "HUT",   "5:1",   "Hut 8 Mining"),
    ("IBB",   "IBB",   "27:1",  "iShares Nasdaq Biotechnology ETF"),
    ("IBIT",  "IBIT",  "10:1",  "iShares Bitcoin Trust ETF"),
    ("IBM",   "IBM",   "15:1",  "IBM"),
    ("IBN",   "IBN",   "1:1",   "ICICI Bank (ADR)"),
    ("ICLN",  "ICLN",  "5:1",   "iShares Global Clean Energy ETF"),
    ("IEMG",  "IEMG",  "12:1",  "iShares Core MSCI EM ETF"),
    ("IEUR",  "IEUR",  "11:1",  "iShares Core MSCI Europe ETF"),
    ("IFF",   "IFF",   "12:1",  "Intl Flavors & Fragrances"),
    ("IJH",   "IJH",   "12:1",  "iShares Core S&P Mid-Cap ETF"),
    ("ILF",   "ILF",   "6:1",   "iShares Latin America 40 ETF"),
    ("INFY",  "INFY",  "1:1",   "Infosys (ADR)"),
    ("ING",   "ING",   "3:1",   "ING Groep (ADR)"),
    ("INTC",  "INTC",  "5:1",   "Intel"),
    ("IP",    "IP",    "4:1",   "International Paper"),
    ("IREN",  "IREN",  "12:1",  "IREN"),
    ("ISRG",  "ISRG",  "90:1",  "Intuitive Surgical"),
    ("ITA",   "ITA",   "50:1",  "iShares US Aerospace & Defense ETF"),
    ("ITUB",  "ITUB",  "1:1",   "Itau Unibanco (ADR)"),
    ("IVE",   "IVE",   "40:1",  "iShares S&P 500 Value ETF"),
    ("IVW",   "IVW",   "20:1",  "iShares S&P 500 Growth ETF"),
    ("IWM",   "IWM",   "10:1",  "iShares Russell 2000 ETF"),
    ("JCI",   "JCI",   "2:1",   "Johnson Controls"),
    ("JD",    "JD",    "4:1",   "JD.com (ADR)"),
    ("JMIA",  "JMIA",  "1:1",   "Jumia (ADR)"),
    ("JNJ",   "JNJ",   "15:1",  "Johnson & Johnson"),
    ("JOYY",  "JOYY",  "5:1",   "JOYY (ADR)"),
    ("JPM",   "JPM",   "15:1",  "JPMorgan Chase"),
    ("KB",    "KB",    "2:1",   "KB Financial (ADR)"),
    ("BITF",  "KEEL",  "1:5",   "Bitfarms"),
    ("KEP",   "KEP",   "1:1",   "Korea Electric Power (ADR)"),
    ("KGC",   "KGC",   "1:1",   "Kinross Gold"),
    ("KMB",   "KMB",   "6:1",   "Kimberly-Clark"),
    ("KO",    "KO",    "5:1",   "Coca-Cola"),
    ("KOF",   "KOFM",  "2:1",   "Coca-Cola Femsa (ADR)"),
    ("LAC",   "LAC",   "1:1",   "Lithium Americas"),
    ("LAAC",  "LAR",   "1:1",   "Lithium Americas (Argentina)"),
    ("LFC",   "LFC",   "2:1",   "China Life Insurance (ADR)"),
    ("LLY",   "LLY",   "56:1",  "Eli Lilly"),
    ("LMT",   "LMT",   "20:1",  "Lockheed Martin"),
    ("LND",   "LND",   "1:1",   "BrasilAgro (ADR)"),
    ("LRCX",  "LRCX",  "56:1",  "Lam Research"),
    ("LVS",   "LVS",   "2:1",   "Las Vegas Sands"),
    ("LYG",   "LYO",   "2:1",   "Lloyds Banking (ADR)"),
    ("MA",    "MA",    "33:1",  "Mastercard"),
    ("MCD",   "MCD",   "24:1",  "McDonald's"),
    ("MDLZ",  "MDLZ",  "15:1",  "Mondelez"),
    ("MDT",   "MDT",   "4:1",   "Medtronic"),
    ("MELI",  "MELI",  "120:1", "MercadoLibre"),
    ("META",  "META",  "24:1",  "Meta Platforms"),
    ("MFG",   "MFG",   "1:1",   "Mizuho Financial (ADR)"),
    ("MMC",   "MMC",   "16:1",  "Marsh & McLennan"),
    ("MMM",   "MMM",   "10:1",  "3M"),
    ("MO",    "MO",    "4:1",   "Altria"),
    ("MOS",   "MOS",   "5:1",   "Mosaic"),
    ("MP",    "MP",    "10:1",  "MP Materials"),
    ("MRK",   "MRK",   "5:1",   "Merck"),
    ("MRNA",  "MRNA",  "19:1",  "Moderna"),
    ("MRVL",  "MRVL",  "14:1",  "Marvell"),
    ("MSFT",  "MSFT",  "30:1",  "Microsoft"),
    ("MSI",   "MSI",   "20:1",  "Motorola Solutions"),
    ("MSTR",  "MSTR",  "20:1",  "MicroStrategy"),
    ("MU",    "MU",    "5:1",   "Micron"),
    ("MUFG",  "MUFG",  "1:1",   "Mitsubishi UFJ (ADR)"),
    ("MUX",   "MUX",   "2:1",   "McEwen Mining"),
    ("NBIS",  "NBIS",  "27:1",  "Nebius Group"),
    ("NEE",   "NEE",   "19:1",  "NextEra Energy"),
    ("NEM",   "NEM",   "3:1",   "Newmont"),
    ("NFLX",  "NFLX",  "48:1",  "Netflix"),
    ("NG",    "NG",    "1:4",   "Novagold"),
    ("NGG",   "NGG",   "2:1",   "National Grid (ADR)"),
    ("NIO",   "NIO",   "4:1",   "NIO (ADR)"),
    ("NKE",   "NKE",   "12:1",  "Nike"),
    ("NMR",   "NMR",   "1:1",   "Nomura (ADR)"),
    ("NOK",   "NOKA",  "1:1",   "Nokia (ADR)"),
    ("NOW",   "NOW",   "172:1", "ServiceNow"),
    ("NSANY", "NSAN",  "1:1",   "Nissan (ADR)"),
    ("NTES",  "NTES",  "14:1",  "NetEase (ADR)"),
    ("NUE",   "NUE",   "16:1",  "Nucor"),
    ("NVDA",  "NVDA",  "24:1",  "NVIDIA"),
    ("NVO",   "NVO",   "7:1",   "Novo Nordisk (ADR)"),
    ("NVS",   "NVS",   "4:1",   "Novartis (ADR)"),
    ("NXE",   "NXE",   "1:1",   "NexGen Energy"),
    ("O",     "O",     "13:1",  "Realty Income"),
    ("OKLO",  "OKLO",  "28:1",  "Oklo"),
    ("ONDS",  "ONDS",  "2:1",   "Ondas Holdings"),
    ("ORAN",  "ORAN",  "1:1",   "Orange (ADR)"),
    ("ORCL",  "ORCL",  "3:1",   "Oracle"),
    ("ORLY",  "ORLY",  "222:1", "O'Reilly Automotive"),
    ("OXY",   "OXY",   "5:1",   "Occidental Petroleum"),
    ("PAAS",  "PAAS",  "3:1",   "Pan American Silver"),
    ("PAC",   "PAC",   "16:1",  "Grupo Aeroportuario Pacifico (ADR)"),
    ("PAGS",  "PAGS",  "3:1",   "PagSeguro"),
    ("PANW",  "PANW",  "50:1",  "Palo Alto Networks"),
    ("PATH",  "PATH",  "2:1",   "UiPath"),
    ("PBI",   "PBI",   "1:1",   "Pitney Bowes"),
    ("PBR",   "PBR",   "1:1",   "Petrobras (ADR)"),
    ("PCAR",  "PCAR",  "3:1",   "Paccar"),
    ("PCRFY", "PCRF",  "2:1",   "Panasonic (ADR)"),
    ("PDD",   "PDD",   "25:1",  "PDD Holdings"),
    ("PEP",   "PEP",   "18:1",  "PepsiCo"),
    ("PFE",   "PFE",   "4:1",   "Pfizer"),
    ("PG",    "PG",    "15:1",  "Procter & Gamble"),
    ("PHG",   "PHG",   "5:1",   "Philips (ADR)"),
    ("PINS",  "PINS",  "7:1",   "Pinterest"),
    ("PKX",   "PKS",   "3:1",   "POSCO (ADR)"),
    ("PLTR",  "PLTR",  "3:1",   "Palantir"),
    ("PM",    "PM",    "18:1",  "Philip Morris Intl"),
    ("PSO",   "PSO",   "1:1",   "Pearson (ADR)"),
    ("PSQ",   "PSQ",   "8:1",   "ProShares Short QQQ ETF"),
    ("PSX",   "PSX",   "6:1",   "Phillips 66"),
    ("PYPL",  "PYPL",  "8:1",   "PayPal"),
    ("QCOM",  "QCOM",  "11:1",  "Qualcomm"),
    ("QQQ",   "QQQ",   "20:1",  "Invesco QQQ Trust ETF"),
    ("RACE",  "RACE",  "83:1",  "Ferrari"),
    ("RBLX",  "RBLX",  "2:1",   "Roblox"),
    ("RGTI",  "RGTI",  "2:1",   "Rigetti Computing"),
    ("RIO",   "RIO",   "8:1",   "Rio Tinto (ADR)"),
    ("RIOT",  "RIOT",  "3:1",   "Riot Platforms"),
    ("RKLB",  "RKLB",  "12:1",  "Rocket Lab"),
    ("ROKU",  "ROKU",  "13:1",  "Roku"),
    ("ROST",  "ROST",  "41:1",  "Ross Stores"),
    ("RSP",   "RSP",   "30:1",  "Invesco S&P 500 Equal Weight ETF"),
    ("RTX",   "RTX",   "5:1",   "RTX (Raytheon)"),
    ("SAN",   "SAN",   "1:4",   "Banco Santander (ADR)"),
    ("SAP",   "SAP",   "6:1",   "SAP (ADR)"),
    ("SATL",  "SATL",  "1:1",   "Satellogic"),
    ("SBS",   "SBS",   "1:2",   "Sabesp (ADR)"),
    ("SBUX",  "SBUX",  "12:1",  "Starbucks"),
    ("SCCO",  "SCCO",  "2:1",   "Southern Copper"),
    ("SCHW",  "SCHW",  "13:1",  "Charles Schwab"),
    ("SDA",   "SDA",   "2:1",   "SunCar Technology"),
    ("SE",    "SE",    "32:1",  "Sea Ltd"),
    ("SH",    "SH",    "8:1",   "ProShares Short S&P500 ETF"),
    ("SHEL",  "SHEL",  "2:1",   "Shell (ADR)"),
    ("SHOP",  "SHOP",  "107:1", "Shopify"),
    ("SID",   "SID",   "1:8",   "CSN (ADR)"),
    ("SIEGY", "SIEGY", "3:1",   "Siemens (ADR)"),
    ("SLB",   "SLB",   "3:1",   "Schlumberger"),
    ("SLV",   "SLV",   "6:1",   "iShares Silver Trust ETF"),
    ("SMH",   "SMH",   "50:1",  "VanEck Semiconductor ETF"),
    ("SNA",   "SNA",   "6:1",   "Snap-on"),
    ("SNAP",  "SNAP",  "1:1",   "Snap Inc"),
    ("SNDK",  "SNDK",  "170:1", "SanDisk"),
    ("SNOW",  "SNOW",  "30:1",  "Snowflake"),
    ("SONY",  "SONY",  "8:1",   "Sony (ADR)"),
    ("SPCE",  "SPCE",  "1:2",   "Virgin Galactic"),
    ("SPGI",  "SPGI",  "45:1",  "S&P Global"),
    ("SPHQ",  "SPHQ",  "14:1",  "Invesco S&P 500 Quality ETF"),
    ("SPOT",  "SPOT",  "28:1",  "Spotify"),
    ("SPXL",  "SPXL",  "25:1",  "Direxion Daily S&P 500 Bull 3X ETF"),
    ("SPY",   "SPY",   "60:1",  "SPDR S&P 500 ETF"),
    ("STLA",  "STLA",  "5:1",   "Stellantis"),
    ("STNE",  "STNE",  "3:1",   "StoneCo"),
    ("SUZ",   "SUZ",   "1:1",   "Suzano (ADR)"),
    ("SWKS",  "SWKS",  "21:1",  "Skyworks Solutions"),
    ("SYY",   "SYY",   "8:1",   "Sysco"),
    ("T",     "T",     "3:1",   "AT&T"),
    ("TCOM",  "TCOM",  "2:1",   "Trip.com (ADR)"),
    ("TEAM",  "TEAM",  "47:1",  "Atlassian"),
    ("TEF",   "TEFO",  "8:1",   "Telefonica (ADR)"),
    ("TEM",   "TEM",   "12:1",  "Tempus AI"),
    ("TS",    "TEN",   "1:1",   "Tenaris (ADR)"),
    ("TGT",   "TGT",   "24:1",  "Target"),
    ("TIMB",  "TIMB",  "1:1",   "TIM (ADR)"),
    ("TJX",   "TJX",   "22:1",  "TJX Companies"),
    ("TM",    "TM",    "15:1",  "Toyota (ADR)"),
    ("TMO",   "TMO",   "22:1",  "Thermo Fisher Scientific"),
    ("TMUS",  "TMUS",  "33:1",  "T-Mobile"),
    ("TQQQ",  "TQQQ",  "25:1",  "ProShares UltraPro QQQ ETF"),
    ("TRIP",  "TRIP",  "2:1",   "Tripadvisor"),
    ("TRV",   "TRVV",  "6:1",   "Travelers"),
    ("TSLA",  "TSLA",  "15:1",  "Tesla"),
    ("TSM",   "TSM",   "9:1",   "TSMC (ADR)"),
    ("TTE",   "TTE",   "3:1",   "TotalEnergies (ADR)"),
    ("TV",    "TV",    "3:1",   "Grupo Televisa (ADR)"),
    ("TWLO",  "TWLO",  "36:1",  "Twilio"),
    ("TX",    "TXR",   "4:1",   "Ternium (ADR)"),
    ("TXN",   "TXN",   "5:1",   "Texas Instruments"),
    ("UAL",   "UAL",   "5:1",   "United Airlines"),
    ("UBER",  "UBER",  "2:1",   "Uber"),
    ("UGP",   "UGP",   "1:1",   "Ultrapar (ADR)"),
    ("UL",    "UL",    "3:1",   "Unilever (ADR)"),
    ("NU",    "UN",    "2:1",   "Nu Holdings"),
    ("UNH",   "UNH",   "33:1",  "UnitedHealth"),
    ("UNP",   "UNP",   "20:1",  "Union Pacific"),
    ("UPST",  "UPST",  "5:1",   "Upstart"),
    ("URA",   "URA",   "5:1",   "Global X Uranium ETF"),
    ("URBN",  "URBN",  "2:1",   "Urban Outfitters"),
    ("USB",   "USB",   "5:1",   "US Bancorp"),
    ("USO",   "USO",   "15:1",  "United States Oil Fund ETF"),
    ("V",     "V",     "18:1",  "Visa"),
    ("VALE",  "VALE",  "2:1",   "Vale (ADR)"),
    ("VEA",   "VEA",   "10:1",  "Vanguard FTSE Developed Markets ETF"),
    ("VIG",   "VIG",   "39:1",  "Vanguard Dividend Appreciation ETF"),
    ("VIST",  "VIST",  "3:1",   "Vista Energy"),
    ("VIV",   "VIV",   "1:1",   "Telefonica Brasil (ADR)"),
    ("VOD",   "VOD",   "1:1",   "Vodafone (ADR)"),
    ("VRSN",  "VRSN",  "6:1",   "Verisign"),
    ("VRTX",  "VRTX",  "101:1", "Vertex Pharmaceuticals"),
    ("VST",   "VST",   "26:1",  "Vistra"),
    ("VXX",   "VXX",   "5:1",   "iPath Series B S&P 500 VIX ETN"),
    ("VZ",    "VZ",    "4:1",   "Verizon"),
    ("WBA",   "WBA",   "3:1",   "Walgreens Boots Alliance"),
    ("WB",    "WBO",   "6:1",   "Weibo"),
    ("WFC",   "WFC",   "5:1",   "Wells Fargo"),
    ("WMT",   "WMT",   "18:1",  "Walmart"),
    ("XLB",   "XLB",   "18:1",  "Materials Select Sector SPDR ETF"),
    ("XLC",   "XLC",   "19:1",  "Comm. Services Select Sector SPDR ETF"),
    ("XLE",   "XLE",   "2:1",   "Energy Select Sector SPDR ETF"),
    ("XLF",   "XLF",   "2:1",   "Financial Select Sector SPDR ETF"),
    ("XLI",   "XLI",   "28:1",  "Industrial Select Sector SPDR ETF"),
    ("XLK",   "XLK",   "46:1",  "Technology Select Sector SPDR ETF"),
    ("XLP",   "XLP",   "16:1",  "Consumer Staples Select Sector SPDR ETF"),
    ("XLRE",  "XLRE",  "9:1",   "Real Estate Select Sector SPDR ETF"),
    ("XLU",   "XLU",   "15:1",  "Utilities Select Sector SPDR ETF"),
    ("XLV",   "XLV",   "29:1",  "Health Care Select Sector SPDR ETF"),
    ("XLY",   "XLY",   "43:1",  "Consumer Discretionary Select Sector SPDR ETF"),
    ("XME",   "XME",   "30:1",  "SPDR S&P Metals & Mining ETF"),
    ("XOM",   "XOM",   "10:1",  "Exxon Mobil"),
    ("XP",    "XP",    "4:1",   "XP Inc"),
    ("XPEV",  "XPEV",  "4:1",   "XPeng (ADR)"),
    ("XRX",   "XROX",  "1:1",   "Xerox"),
    ("XYZ",   "XYZ",   "20:1",  "Block"),
    ("YELP",  "YELP",  "2:1",   "Yelp"),
    ("ZM",    "ZM",    "47:1",  "Zoom"),
]

# -----------------------------------------------------------------------------
# FOREIGN: subyacente NO cotiza en EE.UU. (B3/Frankfurt/LSE). yfinance los puede
# bajar con sufijo (.SA Brasil, .DE Alemania, .IL Londres). Liquidez del CEDEAR
# local suele ser BAJA. Solo se agregan con --include-foreign. Validá ratio y que
# yfinance los cotice antes de confiar.
# -----------------------------------------------------------------------------
FOREIGN = [
    ("ABEV3.SA", "ABEV3", "1:1", "Ambev (B3)"),
    ("BBAS3.SA", "BBAS3", "21:1", "Banco do Brasil (B3)"),
    ("BBDC3.SA", "BBDC3", "1:1", "Bradesco (B3)"),
    ("CSNA3.SA", "CSNA3", "1:1", "CSN (B3)"),
    ("HAPV3.SA", "HAPV3", "1:1", "Hapvida (B3)"),
    ("ITUB3.SA", "ITUB3", "1:1", "Itau (B3)"),
    ("LREN3.SA", "LREN3", "1:1", "Lojas Renner (B3)"),
    ("MGLU3.SA", "MGLU3", "1:1", "Magazine Luiza (B3)"),
    ("NTCO3.SA", "NATU3", "1:1", "Natura (B3)"),
    ("PETR3.SA", "PETR3", "1:1", "Petrobras (B3)"),
    ("PRIO3.SA", "PRIO3", "2:1", "PetroRio (B3)"),
    ("RENT3.SA", "RENT3", "2:1", "Localiza (B3)"),
    ("SBSP3.SA", "SBSP3", "1:1", "Sabesp (B3)"),
    ("SUZB3.SA", "SUZB3", "1:1", "Suzano (B3)"),
    ("TIMS3.SA", "TIMS3", "1:1", "TIM (B3)"),
    ("VALE3.SA", "VALE3", "1:1", "Vale (B3)"),
    ("VIVT3.SA", "VIVT3", "1:1", "Telefonica Brasil (B3)"),
    ("WEGE3.SA", "WEGE3", "1:1", "WEG (B3)"),
    ("ADS.DE",   "ADS",   "22:1", "Adidas (Frankfurt)"),
    ("BAS.DE",   "BAS",   "2:1",  "BASF (Frankfurt)"),
    ("BAYN.DE",  "BAYN",  "3:1",  "Bayer (Frankfurt)"),
    ("EOAN.DE",  "EOAN",  "6:1",  "E.ON (Frankfurt)"),
    ("MBG.DE",   "MBG",   "4:1",  "Mercedes-Benz (Frankfurt)"),
    ("SMSN.IL",  "SMSN",  "14:1", "Samsung (LSE GDR)"),
]

# CEDEARs del listado que NO se agregan (deslistados / adquiridos / sancionados /
# subyacente sin cotización usable). Se documentan para transparencia.
SKIPPED = {
    "AABA": "Altaba liquidada (2019)",
    "TWTR": "Twitter dejó de cotizar (2022)",
    "CS": "Credit Suisse adquirido por UBS (2023)",
    "AUY": "Yamana Gold adquirida (2023)",
    "MBT": "Mobile TeleSystems (Rusia) deslistado de NYSE",
    "PTR": "PetroChina deslistado de NYSE (2022)",
    "SNP": "Sinopec deslistado de NYSE (2023)",
    "SI": "Silvergate en quiebra/deslistado (2024)",
    "TTM": "Tata Motors ADR deslistado (2023)",
    "SHPW": "Shapeways en quiebra (2024)",
    "ATAD": "Tatneft (GDR Londres, Rusia) - ilíquido/sancionado",
    "LKOD": "Lukoil (GDR Londres, Rusia) - ilíquido/sancionado",
    "OGZD": "Gazprom (GDR Londres, Rusia) - ilíquido/sancionado",
    "NLM": "Novolipetsk (GDR Londres, Rusia) - ilíquido/sancionado",
    "HHPD": "Hon Hai (GDR Londres) - sin símbolo yfinance líquido",
    "NECI": "NEC (Frankfurt) - sin símbolo yfinance líquido",
    "YZCA": "Yanzhou Coal (OTC) - sin símbolo yfinance líquido",
    "RCTB4": "Telebras (Bovespa) - ratio 1:1000, ilíquido",
    "BSN": "Danone (listado raro en BYMA) - validar aparte",
    "TILAY": "Telecom Italia (ADR confuso) - validar aparte",
}


def parse_ratio(s):
    a, b = s.split(":")
    return round(float(a) / float(b), 6)


def read_csv_col(path, col):
    """Lee una columna de un CSV; devuelve lista de filas (dicts) y el orden."""
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser(description="Amplía el universo de CEDEARs.")
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--dry-run", action="store_true",
                    help="muestra el informe sin escribir archivos")
    ap.add_argument("--include-foreign", action="store_true",
                    help="agrega también B3/Frankfurt/LSE (.SA/.DE/.IL)")
    args = ap.parse_args()

    uni_path = os.path.join(args.data_dir, "universe_cedears.csv")
    rat_path = os.path.join(args.data_dir, "ratios_cedears.csv")

    table = list(CORE)
    if args.include_foreign:
        table += FOREIGN

    # --- Estado actual (lo respetamos tal cual) ------------------------------
    existing_uni_rows = read_csv_col(uni_path, "ticker")
    existing_uni = {(r.get("ticker") or "").strip().upper()
                    for r in existing_uni_rows if (r.get("ticker") or "").strip()}

    existing_rat_rows = read_csv_col(rat_path, "ticker")
    existing_rat = {}
    for r in existing_rat_rows:
        t = (r.get("ticker") or "").strip().upper()
        if t:
            existing_rat[t] = (r.get("ratio") or "").strip()

    # --- Fusión --------------------------------------------------------------
    new_uni, new_rat, corrected, conflicts = [], [], [], []
    for yf, byma, ratio_str, name in table:
        yf_u = yf.upper()
        if yf_u not in existing_uni:
            new_uni.append(yf)
        if yf_u not in existing_rat:
            new_rat.append((yf, parse_ratio(ratio_str)))
        if yf.upper() != byma.upper():
            corrected.append((byma, yf, name))
        # aviso si tu ratio ya cargado difiere del del snapshot (no lo piso)
        if yf_u in existing_rat:
            try:
                if abs(float(existing_rat[yf_u]) - parse_ratio(ratio_str)) > 1e-6:
                    conflicts.append((yf, existing_rat[yf_u], parse_ratio(ratio_str)))
            except ValueError:
                pass

    final_uni = sorted(existing_uni | {t.upper() for t in new_uni})
    final_rat = dict(existing_rat)
    for t, r in new_rat:
        final_rat.setdefault(t.upper(), r)

    # --- Informe -------------------------------------------------------------
    print(f"\nFuente: {SOURCE}")
    print(f"Snapshot: {SNAPSHOT_DATE}  |  modo: "
          f"{'CORE+FOREIGN' if args.include_foreign else 'CORE'}"
          f"{'  (DRY-RUN)' if args.dry_run else ''}\n")
    print(f"Universo:  {len(existing_uni):>3} actuales  +{len(new_uni):>3} nuevos"
          f"  = {len(final_uni)} total")
    print(f"Ratios:    {len(existing_rat):>3} actuales  +{len(new_rat):>3} nuevos"
          f"  = {len(final_rat)} total")

    if new_uni:
        print(f"\nNuevos tickers ({len(new_uni)}):")
        print("  " + ", ".join(sorted(t.upper() for t in new_uni)))

    if corrected:
        print(f"\nSímbolos corregidos BYMA -> yfinance ({len(corrected)}) "
              f"-- revisalos:")
        for byma, yf, name in sorted(corrected):
            print(f"  {byma:<7} -> {yf:<9} {name}")

    if conflicts:
        print(f"\n[!] Ratios distintos a los que ya tenías (NO los pisé):")
        for t, tuyo, snap in conflicts:
            print(f"  {t:<7} tuyo={tuyo}  snapshot={snap}")

    print(f"\nSe saltearon {len(SKIPPED)} CEDEARs (deslistados/ilíquidos). "
          f"Corré con -h para ver el detalle en el código (dict SKIPPED).")

    if args.dry_run:
        print("\nDRY-RUN: no escribí nada.\n")
        return

    # --- Escritura (con backup) ---------------------------------------------
    os.makedirs(args.data_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    for p in (uni_path, rat_path):
        if os.path.exists(p):
            shutil.copy2(p, f"{p}.{stamp}.bak")

    with open(uni_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ticker"])
        for t in final_uni:
            w.writerow([t])

    with open(rat_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "ratio"])
        for t in sorted(final_rat):
            r = final_rat[t]
            w.writerow([t, f"{r:g}" if isinstance(r, float) else r])

    print(f"\nListo. Backups: *.{stamp}.bak")
    print("Ahora: python portfolio_research.py update   (y luego  funds)")
    print("Recordá validar los ratios nuevos contra Comafi/BYMA para el "
          "precio en ARS.\n")


if __name__ == "__main__":
    main()
