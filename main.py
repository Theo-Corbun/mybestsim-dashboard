import streamlit as st
from modules.datavolume import (
    get_data_tier_distribution,
    get_validity_distribution,
    get_volume_metrics,
)
from modules.parser import load_and_merge_data
from modules.pricing import get_pricing_metrics
from modules.visualization import (
    render_bonus_analytics_section,
    render_provider_distribution_section,
)


# Configuration generale de la page Streamlit
st.set_page_config(
    page_title="MyBestSim - Dashboard Analyse Catalogue eSIM",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def get_cached_catalogue(data_dir="data"):
    """
    Mise en cache du chargement des fichiers CSV pour optimiser les performances
    lors de l'utilisation des filtres interactifs.
    """
    return load_and_merge_data(data_dir)


def render_sidebar_filters(df):
    """
    Genere la barre laterale de filtres et retourne le DataFrame filtre.
    Par defaut, l'ensemble du catalogue (18 fournisseurs) est selectionne.
    """

    st.sidebar.header("Filtres d'exploration")
    st.sidebar.markdown(
        "Utilisez ces filtres pour affiner l'analyse. "
        "Par defaut, la totalite du catalogue est affichee."
    )

    # Filtre par fournisseur
    all_providers = sorted(df["provider"].unique().tolist())
    selected_providers = st.sidebar.multiselect(
        "Fournisseurs",
        options=all_providers,
        default=all_providers,
    )

    # Filtre par destination
    all_countries = sorted(df["country_name"].unique().tolist())
    selected_countries = st.sidebar.multiselect(
        "Destinations (Pays / Zones)",
        options=all_countries,
        default=[],
        help="Laissez vide pour inclure toutes les destinations.",
    )

    # Filtre par technologie reseau
    all_networks = sorted(df["network"].unique().tolist())
    selected_networks = st.sidebar.multiselect(
        "Technologie Reseau",
        options=all_networks,
        default=all_networks,
    )

    # Filtre par type de forfait (Fixe vs Illimite)
    plan_type = st.sidebar.radio(
        "Type d'enveloppe Data",
        options=["Tous les forfaits", "Volume fixe (Go) uniquement", "Illimite uniquement"],
        index=0,
    )

    # Application des filtres sur le DataFrame
    filtered_df = df[df["provider"].isin(selected_providers)]
    filtered_df = filtered_df[filtered_df["network"].isin(selected_networks)]

    if selected_countries:
        filtered_df = filtered_df[filtered_df["country_name"].isin(selected_countries)]

    if plan_type == "Volume fixe (Go) uniquement":
        filtered_df = filtered_df[filtered_df["data_gb"].notna()]
    elif plan_type == "Illimite uniquement":
        filtered_df = filtered_df[filtered_df["data_gb"].isna()]

    return filtered_df


def main():
    """
    Fonction principale orchestrant l'affichage des indicateurs cles et des modules.
    """

    st.title("MyBestSim - Tableau de bord d'analyse des offres eSIM")
    st.markdown(
        "Automatisation de l'analyse statistique quotidienne des catalogues fournisseurs eSIM."
    )

    # Etape 1 : Chargement des donnees via le module parser
    try:
        raw_df = get_cached_catalogue("data")
    except Exception as error:
        st.error(f"Erreur critique lors du chargement des donnees : {error}")
        st.info(
            "Assurez-vous que les 18 fichiers CSV sont bien presents dans le dossier 'data/' a la racine du projet."
        )
        return

    # Etape 2 : Application des filtres de la barre laterale
    df = render_sidebar_filters(raw_df)

    if df.empty:
        st.warning(
            "Aucun produit ne correspond aux criteres de filtrage selectionnes. "
            "Veuillez elargir votre selection dans le menu lateral."
        )
        return

    # Etape 3 : Calcul des metriques via les modules specialises
    volume_metrics = get_volume_metrics(df)
    pricing_metrics = get_pricing_metrics(df, high_price_threshold=100.0)
    tier_distribution = get_data_tier_distribution(df)
    validity_distribution = get_validity_distribution(df)

    st.markdown("---")
    st.subheader("Indicateurs cles du catalogue (KPIs obligatoires)")

    # Ligne 1 des indicateurs principaux (Questions 1 a 5 du test)
    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

    with kpi_col1:
        st.metric(
            label="1. Total cartes eSIM",
            value=f"{volume_metrics['total_products']}",
            help=f"Reparties sur {volume_metrics['total_providers']} fournisseurs et {volume_metrics['total_countries']} destinations.",
        )

    with kpi_col2:
        st.metric(
            label="2. Produits > 100 EUR",
            value=f"{pricing_metrics['count_expensive']}",
            delta=f"{pricing_metrics['percentage_expensive']} % du total",
            delta_color="off",
        )

    with kpi_col3:
        st.metric(
            label="3. Fourchette de prix",
            value=f"{pricing_metrics['min_price']} - {pricing_metrics['max_price']} EUR",
            help="Prix le plus bas et prix le plus haut observes dans la selection.",
        )

    with kpi_col4:
        st.metric(
            label="4. Moyenne de data / carte",
            value=f"{volume_metrics['mean_data_gb']} Go",
            delta=f"Hors {volume_metrics['unlimited_count']} offres illimitees",
            delta_color="off",
        )

    with kpi_col5:
        st.metric(
            label="5. Prix moyen global",
            value=f"{pricing_metrics['mean_price']} EUR",
            delta=f"Mediane : {pricing_metrics['median_price']} EUR",
            delta_color="off",
        )

    # Ligne 2 des indicateurs complementaires (Bonus)
    st.markdown("#### Indicateurs techniques et financiers complementaires (Bonus)")
    bonus_col1, bonus_col2, bonus_col3, bonus_col4 = st.columns(4)

    with bonus_col1:
        st.metric(
            label="Cout moyen par Go",
            value=f"{pricing_metrics['mean_cost_per_gb']} EUR / Go",
            delta=f"Mediane : {pricing_metrics['median_cost_per_gb']} EUR / Go",
            delta_color="off",
        )

    with bonus_col2:
        st.metric(
            label="Offres Data Illimitee",
            value=f"{volume_metrics['unlimited_count']} cartes",
            delta=f"{volume_metrics['unlimited_percentage']} % du catalogue",
            delta_color="off",
        )

    with bonus_col3:
        st.metric(
            label="Compatibilite 5G",
            value=f"{volume_metrics['network_5g_percentage']} %",
            delta=f"{volume_metrics['network_5g_count']} cartes 5G",
            delta_color="off",
        )

    with bonus_col4:
        st.metric(
            label="Offres Rechargeables (Top-up)",
            value=f"{volume_metrics['topup_available_percentage']} %",
            delta=f"{volume_metrics['topup_available_count']} cartes",
            delta_color="off",
        )

    # Detail de la fourchette de prix et des produits > 100 EUR
    with st.expander("Voir le detail des prix extremes et la liste des produits a plus de 100 EUR"):
        min_prod = pricing_metrics["min_product"]
        max_prod = pricing_metrics["max_product"]

        if min_prod and max_prod:
            st.write(
                f"- **Produit le moins cher :** {min_prod['product_name']} "
                f"(Fournisseur : {min_prod['provider']}, SKU : {min_prod['sku']}) "
                f"au tarif de **{min_prod['price']:.2f} EUR**."
            )
            st.write(
                f"- **Produit le plus cher :** {max_prod['product_name']} "
                f"(Fournisseur : {max_prod['provider']}, SKU : {max_prod['sku']}) "
                f"au tarif de **{max_prod['price']:.2f} EUR**."
            )

        st.markdown("**Liste des produits dont le prix dépasse strictement 100 EUR :**")
        st.dataframe(
            pricing_metrics["expensive_df"][
                [
                    "sku",
                    "provider",
                    "product_name",
                    "country_name",
                    "data_display",
                    "validity_days",
                    "price",
                    "network",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    # Etape 4 : Repartition par fournisseur (Question 6 du test)
    render_provider_distribution_section(df, high_price_threshold=100.0)

    st.markdown("---")

    # Etape 5 : Statistiques Bonus (Question 7 du test)
    render_bonus_analytics_section(df, tier_distribution, validity_distribution)

    st.markdown("---")

    # Etape 6 : Explorateur de donnees brutes et export CSV
    st.subheader("Explorateur du catalogue unifie")
    if st.checkbox("Afficher l'integralite des lignes du catalogue filtre"):
        st.dataframe(df, use_container_width=True, hide_index=True)

    csv_export = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Telecharger les donnees filtrees au format CSV",
        data=csv_export,
        file_name="catalogue_mybestsim_unifie.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()