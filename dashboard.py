# ============================================================
#  Dashboard News Portefeuille — Streamlit
#  Pré-requis : pip install streamlit yfinance pandas
#  Lancement  : streamlit run dashboard.py
# ============================================================

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# ── Configuration de la page ─────────────────────────────────────────────────
st.set_page_config(
    page_title="News Portefeuille",
    page_icon="📈",
    layout="wide",
)

# ── CSS personnalisé ─────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Carte article */
  .article-card {
    background: #ffffff;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
    border-left: 4px solid #1a73e8;
    box-shadow: 0 1px 6px rgba(0,0,0,.07);
    transition: box-shadow .2s;
  }
  .article-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.12); }
  .article-title { font-size: 1rem; font-weight: 600; color: #1a1a2e; margin-bottom: 6px; }
  .article-meta  { font-size: .8rem; color: #888; }
  .article-meta span { margin-right: 14px; }

  /* Badge ticker */
  .ticker-badge {
    display: inline-block;
    color: #fff;
    font-size: .75rem;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 20px;
    margin-right: 6px;
    vertical-align: middle;
  }

  /* Lien article */
  .read-link {
    display: inline-block;
    background: #1a73e8;
    color: #fff !important;
    text-decoration: none;
    padding: 4px 12px;
    border-radius: 6px;
    font-size: .78rem;
    font-weight: 500;
    margin-top: 8px;
  }
  .read-link:hover { background: #1558b0; }

  /* Masquer le menu burger Streamlit */
  #MainMenu { visibility: hidden; }
  footer     { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Watchlist par défaut ──────────────────────────────────────────────────────
WATCHLIST_DEFAUT = [
    {"nom": "Broadcom",          "ticker": "AVGO"},
    {"nom": "Marvell Tech",      "ticker": "MRVL"},
    {"nom": "Credo Technology",  "ticker": "CRDO"},
    {"nom": "Intel Corp",        "ticker": "INTC"},
    {"nom": "Poet Technologies", "ticker": "POET"},
]

COULEURS = [
    "#1a73e8", "#e8710a", "#0f9d58", "#6c3483",
    "#c0392b", "#2471a3", "#117a65", "#784212",
]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Paramètres")

    st.subheader("Ma Watchlist")
    st.caption("Format : NOM,TICKER — une ligne par action")

    watchlist_text = st.text_area(
        label="Watchlist",
        value="\n".join(f"{w['nom']},{w['ticker']}" for w in WATCHLIST_DEFAUT),
        height=200,
        label_visibility="collapsed",
    )

    max_articles = st.slider("Articles par valeur", 1, 10, 5)

    actualiser = st.button("🔄 Actualiser les news", use_container_width=True, type="primary")

    st.divider()
    st.caption("Source : Yahoo Finance · yfinance")

# ── Parse watchlist ───────────────────────────────────────────────────────────
def parse_watchlist(texte: str) -> list:
    items = []
    for ligne in texte.strip().splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#"):
            continue
        parts = ligne.split(",")
        if len(parts) >= 2:
            items.append({"nom": parts[0].strip(), "ticker": parts[1].strip().upper()})
    return items

watchlist = parse_watchlist(watchlist_text)

# ── Collecte des news (mise en cache 15 min) ──────────────────────────────────
@st.cache_data(ttl=900, show_spinner=False)
def collecter(watchlist_tuple: tuple, max_art: int) -> pd.DataFrame:
    rows = []
    for nom, ticker in watchlist_tuple:
        try:
            stock = yf.Ticker(ticker)
            news  = stock.news or []
            for article in news[:max_art]:
                content = article.get("content", {})
                titre   = content.get("title") or article.get("title", "—")
                lien    = (content.get("canonicalUrl", {}).get("url")
                           or article.get("link", "—"))
                source  = (content.get("provider", {}).get("displayName")
                           or article.get("publisher", "—"))
                ts = content.get("pubDate") or article.get("providerPublishTime")
                if isinstance(ts, (int, float)):
                    date_str = datetime.utcfromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
                elif isinstance(ts, str):
                    date_str = ts[:16]
                else:
                    date_str = "—"
                rows.append({
                    "Valeur": nom, "Ticker": ticker,
                    "Date": date_str, "Source": source,
                    "Titre": titre, "Lien": lien,
                })
        except Exception as e:
            st.warning(f"Erreur pour {nom} ({ticker}) : {e}")
    return pd.DataFrame(rows)

# ── En-tête principal ─────────────────────────────────────────────────────────
st.title("📈 News Portefeuille")
st.caption(f"Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y à %H:%M')} · "
           f"{len(watchlist)} valeur(s) · cache 15 min")

if not watchlist:
    st.error("⚠️ Aucune valeur dans la watchlist. Ajoutez des lignes NOM,TICKER dans la barre latérale.")
    st.stop()

# ── Chargement ────────────────────────────────────────────────────────────────
with st.spinner("Chargement des actualités…"):
    wl_tuple = tuple((w["nom"], w["ticker"]) for w in watchlist)
    if actualiser:
        st.cache_data.clear()
    df = collecter(wl_tuple, max_articles)

if df.empty:
    st.warning("Aucune actualité trouvée pour cette sélection.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────
k1, k2, k3 = st.columns(3)
k1.metric("📰 Articles collectés", len(df))
k2.metric("📊 Valeurs couvertes",  df["Valeur"].nunique())
k3.metric("📡 Sources distinctes", df["Source"].nunique())

st.divider()

# ── Filtres ───────────────────────────────────────────────────────────────────
col_f1, col_f2 = st.columns([2, 1])
with col_f1:
    valeurs_filtre = st.multiselect(
        "Filtrer par valeur",
        options=df["Valeur"].unique().tolist(),
        default=df["Valeur"].unique().tolist(),
    )
with col_f2:
    recherche = st.text_input("🔍 Rechercher dans les titres", placeholder="ex: earnings, AI…")

# Appliquer les filtres
df_affiche = df[df["Valeur"].isin(valeurs_filtre)]
if recherche:
    df_affiche = df_affiche[
        df_affiche["Titre"].str.contains(recherche, case=False, na=False)
    ]

st.caption(f"{len(df_affiche)} article(s) affiché(s)")
st.divider()

# ── Onglets par valeur ────────────────────────────────────────────────────────
valeurs_affichees = [v for v in df_affiche["Valeur"].unique()]

if not valeurs_affichees:
    st.info("Aucun article ne correspond aux filtres.")
    st.stop()

tabs = st.tabs([f"  {v}  " for v in valeurs_affichees])

for tab, valeur in zip(tabs, valeurs_affichees):
    with tab:
        idx     = [w["nom"] for w in watchlist].index(valeur) if valeur in [w["nom"] for w in watchlist] else 0
        couleur = COULEURS[idx % len(COULEURS)]
        ticker  = df_affiche.loc[df_affiche["Valeur"] == valeur, "Ticker"].iloc[0]
        sous_df = df_affiche[df_affiche["Valeur"] == valeur]

        st.markdown(
            f'<span class="ticker-badge" style="background:{couleur};">{ticker}</span>'
            f'<strong style="font-size:1.1rem;">{valeur}</strong> · '
            f'<span style="color:#888;font-size:.85rem;">{len(sous_df)} article(s)</span>',
            unsafe_allow_html=True,
        )
        st.write("")

        for _, row in sous_df.iterrows():
            lien_bouton = (
                f'<a class="read-link" href="{row["Lien"]}" target="_blank">🔗 Lire l\'article</a>'
                if row["Lien"] and row["Lien"] != "—" else ""
            )
            st.markdown(f"""
            <div class="article-card" style="border-left-color:{couleur};">
              <div class="article-title">{row['Titre']}</div>
              <div class="article-meta">
                <span>📅 {row['Date']}</span>
                <span>📡 {row['Source']}</span>
              </div>
              {lien_bouton}
            </div>
            """, unsafe_allow_html=True)

# ── Export CSV ────────────────────────────────────────────────────────────────
st.divider()
csv = df_affiche.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
st.download_button(
    label="⬇️ Télécharger en CSV",
    data=csv,
    file_name=f"rapport_news_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv",
)
