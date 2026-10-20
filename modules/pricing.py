import pandas as pd


def calculate_cost_per_gb(df):
    """
    Enrichit le DataFrame avec une colonne 'cost_per_gb' representant le cout en EUR par Go.
    Les offres illimitees (ou data_gb est NaN ou <= 0) recoivent une valeur NaN sur cet indicateur.
    """

    analysis_df = df.copy()

    # Initialisation de la colonne avec une valeur nulle
    analysis_df["cost_per_gb"] = float("nan")

    # Masque pour cibler uniquement les forfaits avec un volume de data defini et strictement positif
    valid_data_mask = analysis_df["data_gb"].notna() & (analysis_df["data_gb"] > 0)

    # Calcul du ratio Prix / Data (Go)
    analysis_df.loc[valid_data_mask, "cost_per_gb"] = (
        analysis_df.loc[valid_data_mask, "price"]
        / analysis_df.loc[valid_data_mask, "data_gb"]
    )

    return analysis_df


def get_pricing_metrics(df, high_price_threshold=100.0):
    """
    Calcule l'ensemble des indicateurs financiers globaux du catalogue.
    Le parametre high_price_threshold est fixe par defaut a 100.0 EUR.
    """

    if df.empty:
        return {
            "min_price": 0.0,
            "max_price": 0.0,
            "mean_price": 0.0,
            "median_price": 0.0,
            "std_price": 0.0,
            "count_expensive": 0,
            "percentage_expensive": 0.0,
            "mean_cost_per_gb": 0.0,
            "median_cost_per_gb": 0.0,
            "min_product": None,
            "max_product": None,
            "expensive_df": pd.DataFrame(),
        }

    # Enrichissement avec le cout par Go
    enriched_df = calculate_cost_per_gb(df)

    # Calcul des statistiques de prix globales
    min_price = float(enriched_df["price"].min())
    max_price = float(enriched_df["price"].max())
    mean_price = float(enriched_df["price"].mean())
    median_price = float(enriched_df["price"].median())
    std_price = float(enriched_df["price"].std())

    # Identification des produits correspondant aux bornes minimale et maximale
    min_product_row = enriched_df.loc[enriched_df["price"].idxmin()]
    max_product_row = enriched_df.loc[enriched_df["price"].idxmax()]

    # Filtrage des produits strictement superieurs au seuil (100 EUR par defaut)
    expensive_df = enriched_df[enriched_df["price"] > high_price_threshold].sort_values(
        by="price", ascending=False
    )
    count_expensive = int(len(expensive_df))
    percentage_expensive = (count_expensive / len(enriched_df)) * 100.0

    # Statistiques sur le cout par Go (hors forfaits illimites)
    mean_cost_per_gb = float(enriched_df["cost_per_gb"].mean())
    median_cost_per_gb = float(enriched_df["cost_per_gb"].median())

    pricing_summary = {
        "min_price": round(min_price, 2),
        "max_price": round(max_price, 2),
        "mean_price": round(mean_price, 2),
        "median_price": round(median_price, 2),
        "std_price": round(std_price, 2),
        "count_expensive": count_expensive,
        "percentage_expensive": round(percentage_expensive, 2),
        "mean_cost_per_gb": round(mean_cost_per_gb, 2),
        "median_cost_per_gb": round(median_cost_per_gb, 2),
        "min_product": min_product_row.to_dict(),
        "max_product": max_product_row.to_dict(),
        "expensive_df": expensive_df,
    }

    return pricing_summary


def get_provider_pricing_breakdown(df, high_price_threshold=100.0):
    """
    Genere un tableau recapitulatif des indicateurs financiers agreges par fournisseur.
    """

    enriched_df = calculate_cost_per_gb(df)

    provider_pricing = (
        enriched_df.groupby("provider", as_index=False)
        .agg(
            nombre_produits=("sku", "count"),
            prix_min=("price", "min"),
            prix_moyen=("price", "mean"),
            prix_median=("price", "median"),
            prix_max=("price", "max"),
            produits_sup_100=(
                "price",
                lambda s: int((s > high_price_threshold).sum()),
            ),
            cout_moyen_par_go=("cost_per_gb", "mean"),
        )
        .sort_values(by="cout_moyen_par_go", ascending=True)
    )

    # Arrondi des colonnes numeriques pour la lisibilite
    numeric_cols = ["prix_min", "prix_moyen", "prix_median", "prix_max", "cout_moyen_par_go"]
    provider_pricing[numeric_cols] = provider_pricing[numeric_cols].round(2)

    return provider_pricing