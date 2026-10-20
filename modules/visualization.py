import pandas as pd
import streamlit as st
from modules.pricing import calculate_cost_per_gb


def get_provider_summary_table(df, high_price_threshold=100.0):
    """
    Construit le tableau complet de repartition et de performance par fournisseur.
    """

    if df.empty:
        return pd.DataFrame()

    enriched_df = calculate_cost_per_gb(df)
    total_cards = len(enriched_df)

    summary = (
        enriched_df.groupby("provider", as_index=False)
        .agg(
            Nombre_Cartes=("sku", "count"),
            Prix_Min_EUR=("price", "min"),
            Prix_Moyen_EUR=("price", "mean"),
            Prix_Max_EUR=("price", "max"),
            Cartes_Sup_100_EUR=(
                "price",
                lambda s: int((s > high_price_threshold).sum()),
            ),
            Data_Moyenne_Go=("data_gb", "mean"),
            Cartes_Illimitees=("data_gb", lambda s: int(s.isna().sum())),
            Cout_Moyen_Go_EUR=("cost_per_gb", "mean"),
            Part_5G_Pct=(
                "network",
                lambda s: (s.str.upper() == "5G").mean() * 100.0,
            ),
            Destinations=("country_name", "nunique"),
        )
        .sort_values(by="Nombre_Cartes", ascending=False)
    )

    summary["Part_Catalogue_Pct"] = (
        (summary["Nombre_Cartes"] / total_cards) * 100.0
    ).round(2)

    # Arrondi des valeurs decimales
    cols_to_round = [
        "Prix_Min_EUR",
        "Prix_Moyen_EUR",
        "Prix_Max_EUR",
        "Data_Moyenne_Go",
        "Cout_Moyen_Go_EUR",
        "Part_5G_Pct",
    ]
    summary[cols_to_round] = summary[cols_to_round].round(2)

    # Reorganisation de l'ordre des colonnes pour la lecture
    ordered_columns = [
        "provider",
        "Nombre_Cartes",
        "Part_Catalogue_Pct",
        "Prix_Min_EUR",
        "Prix_Moyen_EUR",
        "Prix_Max_EUR",
        "Cartes_Sup_100_EUR",
        "Data_Moyenne_Go",
        "Cartes_Illimitees",
        "Cout_Moyen_Go_EUR",
        "Part_5G_Pct",
        "Destinations",
    ]

    summary = summary[ordered_columns].rename(columns={"provider": "Fournisseur"})

    return summary.reset_index(drop=True)


def render_provider_distribution_section(df, high_price_threshold=100.0):
    """
    Affiche les graphiques de repartition par fournisseur ainsi que le tableau comparatif.
    """

    st.subheader("Repartition du catalogue par fournisseur")

    summary_df = get_provider_summary_table(df, high_price_threshold)

    if summary_df.empty:
        st.warning("Aucune donnee disponible pour afficher la repartition par fournisseur.")
        return

    col_chart_left, col_chart_right = st.columns(2)

    with col_chart_left:
        st.markdown("**Nombre de cartes eSIM par fournisseur**")
        chart_count_df = summary_df.set_index("Fournisseur")[["Nombre_Cartes"]]
        st.bar_chart(chart_count_df)

    with col_chart_right:
        st.markdown("**Cout moyen par Go (EUR / Go) par fournisseur**")
        chart_cost_df = (
            summary_df.sort_values(by="Cout_Moyen_Go_EUR", ascending=True)
            .set_index("Fournisseur")[["Cout_Moyen_Go_EUR"]]
        )
        st.bar_chart(chart_cost_df)

    st.markdown("**Tableau synthétique de performance par fournisseur**")
    st.dataframe(summary_df, use_container_width=True, hide_index=True)


def render_bonus_analytics_section(df, tier_df, validity_df):
    """
    Affiche les analyses complementaires (Bonus) : paliers de data, durees de validite et destinations.
    """

    st.subheader("Analyses complementaires (Bonus)")

    col_tier, col_validity = st.columns(2)

    with col_tier:
        st.markdown("**Repartition par enveloppe de donnees**")
        if not tier_df.empty:
            st.bar_chart(tier_df.set_index("data_display")[["nombre_cartes"]])
            st.dataframe(
                tier_df.rename(
                    columns={
                        "data_display": "Forfait Data",
                        "nombre_cartes": "Nombre de cartes",
                        "part_catalogue_pct": "Part (%)",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

    with col_validity:
        st.markdown("**Analyse par duree de validite (jours)**")
        if not validity_df.empty:
            display_validity = validity_df.copy()
            display_validity["validity_label"] = (
                display_validity["validity_days"].astype(str) + " jours"
            )
            st.bar_chart(
                display_validity.set_index("validity_label")[["prix_moyen"]]
            )
            st.dataframe(
                validity_df.rename(
                    columns={
                        "validity_days": "Validite (jours)",
                        "nombre_cartes": "Nombre de cartes",
                        "prix_moyen": "Prix moyen (EUR)",
                        "data_moyenne_go": "Data moyenne (Go)",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

    st.markdown("---")
    st.markdown("**Analyse géographique par destination (Top 15 par volume d'offres)**")

    enriched_df = calculate_cost_per_gb(df)
    country_summary = (
        enriched_df.groupby(["country_code", "country_name"], as_index=False)
        .agg(
            Nombre_Offres=("sku", "count"),
            Fournisseurs_Presents=("provider", "nunique"),
            Prix_Min_EUR=("price", "min"),
            Prix_Moyen_EUR=("price", "mean"),
            Cout_Moyen_Go_EUR=("cost_per_gb", "mean"),
        )
        .sort_values(by=["Nombre_Offres", "Prix_Moyen_EUR"], ascending=[False, True])
    )

    country_summary[["Prix_Min_EUR", "Prix_Moyen_EUR", "Cout_Moyen_Go_EUR"]] = (
        country_summary[["Prix_Min_EUR", "Prix_Moyen_EUR", "Cout_Moyen_Go_EUR"]].round(2)
    )

    st.dataframe(
        country_summary.head(15).rename(
            columns={
                "country_code": "Code ISO",
                "country_name": "Destination",
                "Nombre_Offres": "Nombre d'offres",
                "Fournisseurs_Presents": "Fournisseurs actifs",
                "Prix_Min_EUR": "Prix Min (EUR)",
                "Prix_Moyen_EUR": "Prix Moyen (EUR)",
                "Cout_Moyen_Go_EUR": "Cout Moyen / Go (EUR)",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )