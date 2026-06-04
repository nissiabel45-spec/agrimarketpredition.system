"""
AgriMarket Recommendation Feature
Phase 2: Synthetic Data Generator
Author: AJEICHEK ABEL NISSI (CT23A010)

Generates a realistic user-product interaction matrix based on
actual Agromarket.cm categories and product listings observed
from the live site.

Run:
    python generate_data.py
    # Creates: data/interaction_matrix.csv, data/products.csv
"""

import os
import random
import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

# ---------------------------------------------------------------------------
# Real Agromarket product catalogue (from agromarket.cm/en)
# ---------------------------------------------------------------------------

PRODUCTS = [
    {"id": "2022", "title": "Mangues à vendre",          "category": "fruitsetlegumes"},
    {"id": "2130", "title": "Poireau à vendre",           "category": "fruitsetlegumes"},
    {"id": "2100", "title": "Vente fruits et légumes",    "category": "fruitsetlegumes"},
    {"id": "2026", "title": "Avocats à vendre",           "category": "fruitsetlegumes"},
    {"id": "2101", "title": "Ananas à vendre",            "category": "fruitsetlegumes"},
    {"id": "2014", "title": "Tomate fraîche à vendre",    "category": "fruitsetlegumes"},
    {"id": "2012", "title": "Haricot à vendre",           "category": "fruitsetlegumes"},
    {"id": "2098", "title": "Noix et huile de coco",      "category": "agroalimentaire"},
    {"id": "2109", "title": "Fufu à vendre",              "category": "agroalimentaire"},
    {"id": "2139", "title": "Huile de sésame à vendre",   "category": "agroalimentaire"},
    {"id": "2140", "title": "Huile de ricin à vendre",    "category": "agroalimentaire"},
    {"id": "2134", "title": "Djansang à vendre",          "category": "tubercules"},
    {"id": "2013", "title": "Manioc à vendre",            "category": "tubercules"},
    {"id": "2108", "title": "Épices à vendre",            "category": "tubercules"},
    {"id": "2104", "title": "Traitement pour végétaux",   "category": "traitement"},
    {"id": "2105", "title": "Produits traitement animaux","category": "traitement"},
    {"id": "2096", "title": "Poulets à vendre",           "category": "plantations"},
    {"id": "2095", "title": "Palmeraie à vendre",         "category": "plantations"},
    {"id": "2106", "title": "Cola Bafia à vendre",        "category": "sylviculture"},
    {"id": "2023", "title": "Crevettes sèches à vendre",  "category": "elevage1"},
]

# ---------------------------------------------------------------------------
# User persona profiles (simulate realistic browsing patterns)
# ---------------------------------------------------------------------------

PERSONAS = [
    # (name, preferred_categories, activity_level)
    ("fruit_buyer",     ["fruitsetlegumes"],                        0.8),
    ("food_processor",  ["agroalimentaire", "tubercules"],          0.7),
    ("farmer",          ["traitement", "plantations", "elevage1"],  0.6),
    ("trader",          ["fruitsetlegumes", "agroalimentaire"],     0.9),
    ("general_buyer",   None,                                       0.4),  # browses all
]

# ---------------------------------------------------------------------------
# Build category → product index map
# ---------------------------------------------------------------------------

products_df = pd.DataFrame(PRODUCTS)
products_df.index = range(len(products_df))
cat_to_indices = {}
for i, row in products_df.iterrows():
    cat_to_indices.setdefault(row["category"], []).append(i)

# ---------------------------------------------------------------------------
# Generate interactions
# ---------------------------------------------------------------------------

N_USERS = 500

def score_interaction(base_prob: float) -> float:
    """
    Convert a view probability into a weighted interaction score.
    0  = no interaction
    1  = view only
    2  = view + click contact
    3  = repeat visit (strong signal)
    """
    r = random.random()
    if r > base_prob:
        return 0
    strength = random.random()
    if strength < 0.5:
        return 1
    elif strength < 0.8:
        return 2
    else:
        return 3

records = []
for user_id in range(N_USERS):
    persona_name, pref_cats, activity = random.choice(PERSONAS)

    for prod_idx, prod_row in products_df.iterrows():
        cat = prod_row["category"]

        # Higher probability for preferred categories
        if pref_cats is None:
            prob = activity * 0.3
        elif cat in pref_cats:
            prob = activity * 0.7
        else:
            prob = activity * 0.1

        score = score_interaction(prob)
        if score > 0:
            records.append({
                "user_id":    user_id,
                "product_id": prod_row["id"],
                "product_idx": prod_idx,
                "score":      score,
                "category":   cat,
            })

interactions_df = pd.DataFrame(records)

# ---------------------------------------------------------------------------
# Save outputs
# ---------------------------------------------------------------------------

os.makedirs("data", exist_ok=True)

interactions_df.to_csv("data/interaction_matrix.csv", index=False)
products_df.to_csv("data/products.csv", index=False)

print(f"Generated {len(interactions_df):,} interactions")
print(f"  Users:    {interactions_df['user_id'].nunique()}")
print(f"  Products: {interactions_df['product_id'].nunique()}")
print(f"  Sparsity: {1 - len(interactions_df) / (N_USERS * len(products_df)):.1%}")
print(f"\nSaved to data/interaction_matrix.csv")
print(f"Saved to data/products.csv")
