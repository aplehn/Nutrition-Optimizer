# optimizer_modes.py

MODE_WEIGHTS = {
    "normal": {
        "satiety_score": 1.0,
    },

    "rfk_jr": {
        "satiety_score": 1.0,
        "is_beef": 2.0,
        "Total Fat (g)": 0.8,
        "is_grain": -2.0,
        "Carbs (g)": -0.2,
    },

    "cookie_monster": {
        #"satiety_score": 0.2,
        "is_cookie": 4.0,
        #"is_sweets": 2.0,
        #"Sugars (g)": 1.2,
        #"Carbs (g)": 0.3,
    },

    "bodybuilder": {
        "Protein (g)": 2.0,
        "protein_density": 120.0,
        "satiety_score": 0.5,
        "Calories (kcal)": -0.05,
    },

    "mediterranean": {
        "satiety_score": 0.6,
        "is_fish": 1.5,
        "is_legume": 1.2,
        "is_nut": 1.0,
        "is_seed": 0.8,
        "is_olive_oil": 1.5,
        "is_fruit": 0.8,
        "is_vegetable": 0.8,
        "is_red_meat": -1.2,
    },

    "keto": {
        "Total Fat (g)": 1.3,
        "Protein (g)": 0.8,
        "Carbs (g)": -2.0,
        "Sugars (g)": -2.0,
    },

    "carnivore": {
        "is_red_meat": 2.0,
        "is_chicken": 1.2,
        "Total Fat (g)": 0.8,
        "is_fruit": -1.5,
        "is_vegetable": -1.5,
        "is_grain": -2.0,
        "is_legume": -1.5,
    },

    "bro_science": {
        "Protein (g)": 1.5,
        "is_chicken": 2.5,
        "is_rice": 1.5,
        "is_broccoli": 1.5,
        "Sugars (g)": -1.0,
        "Total Fat (g)": -0.2,
    },

    "college_student": {
        "Calories (kcal)": 0.4,
        "satiety_score": 0.3,
        "Protein (g)": 0.3,
    },

    "biohacker": {
        "satiety_score": 1.0,
        "protein_density": 60.0,
        "is_fish": 1.0,
        "is_fruit": 0.8,
        "is_vegetable": 1.2,
        "Sugars (g)": -0.8,
    },

    "low_calorie": {
        "satiety_score": 0.8,
        "Calories (kcal)": -1.2,
        "protein_density": 50.0,
    },
}


def add_mode_features(foods):
    """
    Adds feature columns used by the different optimizer modes.
    Returns a modified copy of the DataFrame.
    """
    foods = foods.copy()

    foods['is_beef'] = foods['Name'].str.contains(r'beef', case=False, na=False).astype(int)

    foods['is_grain'] = foods['Name'].str.contains(
        r'rice|oat|oats|wheat|bread|pasta|barley|cereal|corn|quinoa|flour',
        case=False, na=False
    ).astype(int)

    foods['is_cookie'] = foods['Name'].str.contains(
        r'cookie|oreo|chocolate chip',
        case=False, na=False
    ).astype(int)

    foods['is_sweets'] = foods['Name'].str.contains(
        r'cake|brownie|donut|ice cream|candy|dessert|chocolate',
        case=False, na=False
    ).astype(int)

    foods['is_fish'] = foods['Name'].str.contains(
        r'salmon|tuna|sardine|mackerel|trout|anchovy|fish',
        case=False, na=False
    ).astype(int)

    foods['is_legume'] = foods['Name'].str.contains(
        r'bean|lentil|chickpea|pea|hummus',
        case=False, na=False
    ).astype(int)

    foods['is_nut'] = foods['Name'].str.contains(
        r'almond|walnut|cashew|pecan|pistachio|hazelnut|nut',
        case=False, na=False
    ).astype(int)

    foods['is_seed'] = foods['Name'].str.contains(
        r'chia|flax|pumpkin seed|sunflower seed|seed',
        case=False, na=False
    ).astype(int)

    foods['is_olive_oil'] = foods['Name'].str.contains(
        r'olive oil|olives',
        case=False, na=False
    ).astype(int)

    foods['is_fruit'] = foods['FoodCategory'].str.contains(
        r'Fruit',
        case=False, na=False
    ).astype(int)

    foods['is_vegetable'] = foods['FoodCategory'].str.contains(
        r'Vegetable',
        case=False, na=False
    ).astype(int)

    foods['is_red_meat'] = foods['Name'].str.contains(
        r'beef|lamb|veal|goat',
        case=False, na=False
    ).astype(int)

    foods['is_chicken'] = foods['Name'].str.contains(
        r'chicken|turkey',
        case=False, na=False
    ).astype(int)

    foods['is_rice'] = foods['Name'].str.contains(
        r'rice',
        case=False, na=False
    ).astype(int)

    foods['is_broccoli'] = foods['Name'].str.contains(
        r'broccoli',
        case=False, na=False
    ).astype(int)

    portion = foods['Portion size (g)'].replace(0, 100)

    foods['protein_density'] = foods['Protein (g)'] / portion
    foods['fat_density'] = foods['Total Fat (g)'] / portion
    foods['carb_density'] = foods['Carbs (g)'] / portion
    foods['sugar_density'] = foods['Sugars (g)'] / portion

    return foods


def apply_mode_scores(foods, mode, mode_weights=MODE_WEIGHTS):
    """
    Build a weighted score column for the selected mode.
    """
    foods = foods.copy()

    if mode not in mode_weights:
        raise ValueError(f"Unknown mode '{mode}'. Available modes: {list(mode_weights.keys())}")

    weights = mode_weights[mode]
    foods['mode_score'] = 0.0

    for feature, weight in weights.items():
        if feature not in foods.columns:
            raise ValueError(f"Feature '{feature}' not found in foods DataFrame.")
        foods['mode_score'] += weight * foods[feature]

    return foods