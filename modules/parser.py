import glob
import os
import pandas as pd


REQUIRED_COLUMNS = [
    "sku",
    "provider",
    "product_name",
    "country_code",
    "country_name",
    "data_gb",
    "data_display",
    "validity_days",
    "price",
    "currency",
    "network",
    "top_up",
]


def load_and_merge_data(data_directory="data"):
    """
    Charge dynamiquement tous les fichiers CSV presents dans le dossier specifie,
    verifie la conformite des colonnes, nettoie les types et retourne un DataFrame unifie.
    """

    # Verification de l'existence du dossier source
    if not os.path.exists(data_directory):
        raise FileNotFoundError(
            f"Le dossier '{data_directory}' est introuvable. Verifiez l'arborescence du projet."
        )

    # Recherche de tous les fichiers CSV dans le dossier
    search_path = os.path.join(data_directory, "*.csv")
    csv_files = sorted(glob.glob(search_path))

    if not csv_files:
        raise FileNotFoundError(
            f"Aucun fichier CSV n'a ete trouve dans le dossier '{data_directory}'."
        )

    dataframes_list = []

    # Lecture individuelle de chaque fichier fournisseur
    for file_path in csv_files:
        try:
            # L'argument keep_default_na=False empeche Pandas de convertir le country_code 'NA'
            # (Amerique du Nord) en valeur nulle (NaN). Seules les chaines vides sont traitees comme NaN.
            temp_df = pd.read_csv(
                file_path,
                keep_default_na=False,
                na_values=[""],
                encoding="utf-8",
            )

            # Verification de la presence des colonnes attendues
            missing_cols = [
                col for col in REQUIRED_COLUMNS if col not in temp_df.columns
            ]
            if missing_cols:
                raise ValueError(
                    f"Colonnes manquantes dans {os.path.basename(file_path)} : {missing_cols}"
                )

            # Ajout du nom du fichier source pour assurer la tracabilite
            temp_df["source_file"] = os.path.basename(file_path)

            dataframes_list.append(temp_df)

        except Exception as error:
            raise RuntimeError(
                f"Erreur lors de la lecture du fichier '{file_path}' : {error}"
            ) from error

    # Fusion de tous les fichiers en un catalogue unique
    master_df = pd.concat(dataframes_list, ignore_index=True)

    # Nettoyage et conversion explicite des types numeriques
    master_df["price"] = pd.to_numeric(master_df["price"], errors="coerce")
    master_df["data_gb"] = pd.to_numeric(master_df["data_gb"], errors="coerce")
    master_df["validity_days"] = pd.to_numeric(
        master_df["validity_days"], errors="coerce"
    )

    # Normalisation des chaines de caracteres pour eviter les espaces parasites
    text_columns = [
        "sku",
        "provider",
        "product_name",
        "country_code",
        "country_name",
        "data_display",
        "currency",
        "network",
        "top_up",
    ]
    for col in text_columns:
        master_df[col] = master_df[col].astype(str).str.strip()

    # Suppression des eventuels doublons stricts sur l'identifiant unique SKU
    master_df = master_df.drop_duplicates(subset=["sku"], keep="first")

    # Suppression des lignes dont le prix serait invalide ou manquant
    master_df = master_df.dropna(subset=["price"]).reset_index(drop=True)

    return master_df