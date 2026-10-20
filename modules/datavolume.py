import pandas as pd


def get_volume_metrics(df):
    """
    Calcule les indicateurs de volume de produits et de quantite de donnees (Go).
    Separe explicitement les offres a volume fixe et les offres illimitees.
    """

    if df.empty:
        return {
            "total_products": 0,
            "total_providers": 0,
            "total_countries": 0,
            "fixed_data_count": 0,
            "unlimited_count": 0,
            "unlimited_percentage": 0.0,
            "mean_data_gb": 0.0,
            "median_data_gb": 0.0,
            "min_data_gb": 0.0,
            "max_data_gb": 0.0,
            "network_5g_count": 0,
            "network_5g_percentage": 0.0,
            "topup_available_count": 0,
            "topup_available_percentage": 0.0,
        }

    total_products = int(len(df))
    total_providers = int(df["provider"].nunique())
    total_countries = int(df["country_name"].nunique())

    # Separation entre les forfaits avec volume en Go et les forfaits Illimites
    fixed_data_df = df[df["data_gb"].notna() & (df["data_gb"] > 0)]
    unlimited_df = df[df["data_gb"].isna()]

    fixed_data_count = int(len(fixed_data_df))
    unlimited_count = int(len(unlimited_df))
    unlimited_percentage = (unlimited_count / total_products) * 100.0

    # Statistiques de volume en Go sur les forfaits a enveloppe fixe
    mean_data_gb = float(fixed_data_df["data_gb"].mean()) if fixed_data_count > 0 else 0.0
    median_data_gb = float(fixed_data_df["data_gb"].median()) if fixed_data_count > 0 else 0.0
    min_data_gb = float(fixed_data_df["data_gb"].min()) if fixed_data_count > 0 else 0.0
    max_data_gb = float(fixed_data_df["data_gb"].max()) if fixed_data_count > 0 else 0.0

    # Statistiques reseau (5G vs 4G) et possibilite de recharge (top_up)
    network_5g_count = int((df["network"].str.upper() == "5G").sum())
    network_5g_percentage = (network_5g_count / total_products) * 100.0

    topup_available_count = int((df["top_up"].str.lower() == "oui").sum())
    topup_available_percentage = (topup_available_count / total_products) * 100.0

    volume_summary = {
        "total_products": total_products,
        "total_providers": total_providers,
        "total_countries": total_countries,
        "fixed_data_count": fixed_data_count,
        "unlimited_count": unlimited_count,
        "unlimited_percentage": round(unlimited_percentage, 2),
        "mean_data_gb": round(mean_data_gb, 2),
        "median_data_gb": round(median_data_gb, 2),
        "min_data_gb": round(min_data_gb, 2),
        "max_data_gb": round(max_data_gb, 2),
        "network_5g_count": network_5g_count,
        "network_5g_percentage": round(network_5g_percentage, 2),
        "topup_available_count": topup_available_count,
        "topup_available_percentage": round(topup_available_percentage, 2),
    }

    return volume_summary


def get_data_tier_distribution(df):
    """
    Calcule la repartition du catalogue par palier de donnees (1 Go, 3 Go, ..., Illimite).
    """

    if df.empty:
        return pd.DataFrame()

    tier_counts = (
        df.groupby(["data_display", "data_gb"], dropna=False)
        .size()
        .reset_index(name="nombre_cartes")
    )

    # Tri logique : par volume numerique croissant, puis Illimite a la fin
    tier_counts["sort_key"] = tier_counts["data_gb"].fillna(999999.0)
    tier_counts = tier_counts.sort_values(by="sort_key", ascending=True).drop(
        columns=["sort_key", "data_gb"]
    )

    tier_counts["part_catalogue_pct"] = (
        (tier_counts["nombre_cartes"] / len(df)) * 100.0
    ).round(2)

    return tier_counts.reset_index(drop=True)


def get_validity_distribution(df):
    """
    Calcule la repartition des produits selon la duree de validite en jours.
    """

    if df.empty:
        return pd.DataFrame()

    validity_counts = (
        df.groupby("validity_days")
        .agg(
            nombre_cartes=("sku", "count"),
            prix_moyen=("price", "mean"),
            data_moyenne_go=("data_gb", "mean"),
        )
        .reset_index()
        .sort_values(by="validity_days", ascending=True)
    )

    validity_counts["prix_moyen"] = validity_counts["prix_moyen"].round(2)
    validity_counts["data_moyenne_go"] = validity_counts["data_moyenne_go"].round(2)

    return validity_counts