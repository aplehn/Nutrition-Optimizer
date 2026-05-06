from copy import deepcopy


# -----------------------------
# Activity multipliers
# -----------------------------
ACTIVITY_FACTORS = {
    "sedentary": 1.20,
    "light": 1.375,
    "moderate": 1.55,
    "very_active": 1.725,
}


# -----------------------------
# Base adult nutrient ranges
# Format: nutrient_name -> (min, max)
# Use None where no upper bound is desired
# -----------------------------
# ALEC_PLEHN_BASE = {
#     'B6_Pyridoxine': (1.3*3, 100),       # mg
#     'B12_Cobalamin': (2.4*3, None),      # mcg
#     'Folate': (400, 1000),             # mcg
#     'Vitamin_A': (900, 3000),          # mcg
#     'Vitamin_C': (90, 2000),           # mg
#     'Vitamin_D': (15*10, None),        # mcg
#     'Vitamin_E': (15, 1000),           # mg
#     'Vitamin_K': (120, None),          # mcg
#     'Iron': (8*10, None),                   # mg
#     'Carbs': (130, None),              # g
#     'Fiber': (25, 70),                 # placeholder; overwritten from calories
#     'Fat': (44, 77),                   # placeholder; overwritten from calories
#     'Saturated_Fat': (0, 20),          # placeholder; overwritten from calories
#     'Omega_3': (1.6, None),            # g
#     'Calcium': (1000*1.2, 2500),           # mg
#     'Magnesium': (420*1.2, None),          # mg
#     'Potassium': (3400, None),         # mg
#     'Sodium': (0, 2300),               # mg
#     'Zinc': (11, 40),                  # mg
#     'Protein': (50, None),             # placeholder; overwritten from weight
# }

ADULT_MALE_BASE = {
    'B6_Pyridoxine': (1.3, 100),       # mg
    'B12_Cobalamin': (2.4, None),      # mcg
    'Folate': (400, 1000),             # mcg
    'Vitamin_A': (900, 3000),          # mcg
    'Vitamin_C': (90, 2000),           # mg
    'Vitamin_D': (15, 100),            # mcg
    'Vitamin_E': (15, 1000),           # mg
    'Vitamin_K': (120, None),          # mcg
    'Iron': (8, 45),                   # mg
    'Carbs': (130, None),              # g
    'Fiber': (25, 70),                 # placeholder; overwritten from calories
    'Fat': (44, 77),                   # placeholder; overwritten from calories
    'Saturated_Fat': (0, 20),          # placeholder; overwritten from calories
    'Omega_3': (1.6, None),            # g
    'Calcium': (1000, 2500),           # mg
    'Magnesium': (420, None),          # mg
    'Potassium': (3400, None),         # mg
    'Sodium': (0, 2300),               # mg
    'Zinc': (11, 40),                  # mg
    'Protein': (50, None),             # placeholder; overwritten from weight
}

ADULT_FEMALE_BASE = {
    'B6_Pyridoxine': (1.3, 100),
    'B12_Cobalamin': (2.4, None),
    'Folate': (400, 1000),
    'Vitamin_A': (700, 3000),
    'Vitamin_C': (75, 2000),
    'Vitamin_D': (15, 100),
    'Vitamin_E': (15, 1000),
    'Vitamin_K': (90, None),
    'Iron': (18, 45),
    'Carbs': (130, None),
    'Fiber': (25, 70),                 # placeholder; overwritten from calories
    'Fat': (44, 77),                   # placeholder; overwritten from calories
    'Saturated_Fat': (0, 20),          # placeholder; overwritten from calories
    'Omega_3': (1.1, None),
    'Calcium': (1000, 2500),
    'Magnesium': (320, None),
    'Potassium': (2600, None),
    'Sodium': (0, 2300),
    'Zinc': (8, 40),
    'Protein': (50, None),             # placeholder; overwritten from weight
}


# -----------------------------
# Child / adolescent age buckets
# These are simplified planning targets
# -----------------------------
CHILD_1_3 = {
    'B6_Pyridoxine': (0.5, 30),
    'B12_Cobalamin': (0.9, None),
    'Folate': (150, 300),
    'Vitamin_A': (300, 600),
    'Vitamin_C': (15, 400),
    'Vitamin_D': (15, 63),
    'Vitamin_E': (6, 200),
    'Vitamin_K': (30, None),
    'Iron': (7, 40),
    'Carbs': (130, None),
    'Fiber': (19, 50),                 # placeholder-ish practical bound
    'Fat': (30, 60),                   # overwritten from calories if desired
    'Saturated_Fat': (0, 15),
    'Omega_3': (0.7, None),
    'Calcium': (700, 2500),
    'Magnesium': (80, None),
    'Potassium': (2000, None),
    'Sodium': (0, 1500),
    'Zinc': (3, 7),
    'Protein': (13, None),
}

CHILD_4_8 = {
    'B6_Pyridoxine': (0.6, 40),
    'B12_Cobalamin': (1.2, None),
    'Folate': (200, 400),
    'Vitamin_A': (400, 900),
    'Vitamin_C': (25, 650),
    'Vitamin_D': (15, 75),
    'Vitamin_E': (7, 300),
    'Vitamin_K': (55, None),
    'Iron': (10, 40),
    'Carbs': (130, None),
    'Fiber': (25, 60),
    'Fat': (35, 70),
    'Saturated_Fat': (0, 18),
    'Omega_3': (0.9, None),
    'Calcium': (1000, 2500),
    'Magnesium': (130, None),
    'Potassium': (2300, None),
    'Sodium': (0, 1900),
    'Zinc': (5, 12),
    'Protein': (19, None),
}

CHILD_9_13_MALE = {
    'B6_Pyridoxine': (1.0, 60),
    'B12_Cobalamin': (1.8, None),
    'Folate': (300, 600),
    'Vitamin_A': (600, 1700),
    'Vitamin_C': (45, 1200),
    'Vitamin_D': (15, 100),
    'Vitamin_E': (11, 600),
    'Vitamin_K': (60, None),
    'Iron': (8, 40),
    'Carbs': (130, None),
    'Fiber': (31, 70),
    'Fat': (40, 85),
    'Saturated_Fat': (0, 22),
    'Omega_3': (1.2, None),
    'Calcium': (1300, 3000),
    'Magnesium': (240, None),
    'Potassium': (2500, None),
    'Sodium': (0, 2200),
    'Zinc': (8, 23),
    'Protein': (34, None),
}

CHILD_9_13_FEMALE = {
    'B6_Pyridoxine': (1.0, 60),
    'B12_Cobalamin': (1.8, None),
    'Folate': (300, 600),
    'Vitamin_A': (600, 1700),
    'Vitamin_C': (45, 1200),
    'Vitamin_D': (15, 100),
    'Vitamin_E': (11, 600),
    'Vitamin_K': (60, None),
    'Iron': (8, 40),
    'Carbs': (130, None),
    'Fiber': (26, 70),
    'Fat': (40, 85),
    'Saturated_Fat': (0, 22),
    'Omega_3': (1.0, None),
    'Calcium': (1300, 3000),
    'Magnesium': (240, None),
    'Potassium': (2300, None),
    'Sodium': (0, 2200),
    'Zinc': (8, 23),
    'Protein': (34, None),
}

TEEN_14_18_MALE = {
    'B6_Pyridoxine': (1.3, 80),
    'B12_Cobalamin': (2.4, None),
    'Folate': (400, 800),
    'Vitamin_A': (900, 2800),
    'Vitamin_C': (75, 1800),
    'Vitamin_D': (15, 100),
    'Vitamin_E': (15, 800),
    'Vitamin_K': (75, None),
    'Iron': (11, 45),
    'Carbs': (130, None),
    'Fiber': (38, 75),
    'Fat': (50, 95),
    'Saturated_Fat': (0, 25),
    'Omega_3': (1.6, None),
    'Calcium': (1300, 3000),
    'Magnesium': (410, None),
    'Potassium': (3000, None),
    'Sodium': (0, 2300),
    'Zinc': (11, 34),
    'Protein': (52, None),
}

TEEN_14_18_FEMALE = {
    'B6_Pyridoxine': (1.2, 80),
    'B12_Cobalamin': (2.4, None),
    'Folate': (400, 800),
    'Vitamin_A': (700, 2800),
    'Vitamin_C': (65, 1800),
    'Vitamin_D': (15, 100),
    'Vitamin_E': (15, 800),
    'Vitamin_K': (75, None),
    'Iron': (15, 45),
    'Carbs': (130, None),
    'Fiber': (26, 70),
    'Fat': (45, 90),
    'Saturated_Fat': (0, 23),
    'Omega_3': (1.1, None),
    'Calcium': (1300, 3000),
    'Magnesium': (360, None),
    'Potassium': (2300, None),
    'Sodium': (0, 2300),
    'Zinc': (9, 34),
    'Protein': (46, None),
}


# -----------------------------
# Helper functions
# -----------------------------
def estimate_energy_kcal(sex, age_years, weight_kg, height_cm, activity_level="moderate"):
    """
    Simple Mifflin-St Jeor approximation.
    Good enough for an optimization class project.
    """
    sex = sex.lower()
    if sex == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age_years + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age_years - 161
    return bmr * ACTIVITY_FACTORS[activity_level]


def get_base_profile(sex, age_years):
    sex = sex.lower()

    if age_years <= 3:
        return deepcopy(CHILD_1_3)
    elif age_years <= 8:
        return deepcopy(CHILD_4_8)
    elif age_years <= 13:
        return deepcopy(CHILD_9_13_MALE if sex == "male" else CHILD_9_13_FEMALE)
    elif age_years <= 18:
        return deepcopy(TEEN_14_18_MALE if sex == "male" else TEEN_14_18_FEMALE)
    else:
        return deepcopy(ADULT_MALE_BASE if sex == "male" else ADULT_FEMALE_BASE)


def apply_life_stage_overrides(ranges, sex, age_years, life_stage):
    """
    Applies overrides for pregnancy / lactation.
    Assumes adult female if pregnant/lactating.
    """
    sex = sex.lower()
    life_stage = life_stage.lower()

    if life_stage == "adult":
        return ranges
    
    if life_stage == "alec plehn":
        ranges['B6_Pyridoxine'] = (1.3*3, 100)       # mg
        ranges['B12_Cobalamin'] = (2.4*3, None)      # mcg
        ranges['Folate'] = (400, 1000)             # mcg
        ranges['Vitamin_A'] = (900, 3000)          # mcg
        ranges['Vitamin_C'] = (90, 2000)           # mg
        ranges['Vitamin_D'] = (15*10, None)        # mcg
        ranges['Vitamin_E'] = (15, 1000)           # mg
        ranges['Vitamin_K'] = (120, None)          # mcg
        ranges['Iron'] = (8*10, None)              # mg
        ranges['Carbs'] = (130, None)              # g
        ranges['Fiber'] = (25, 70)                 # placeholder; overwritten from calories
        ranges['Fat'] = (44, 77)                   # placeholder; overwritten from calories
        ranges['Saturated_Fat'] = (0, 20)          # placeholder; overwritten from calories
        ranges['Omega_3'] = (1.6, None)            # g
        ranges['Calcium'] = (1000*1.2, 2500)       # mg
        ranges['Magnesium'] = (420*1.2, None)      # mg
        ranges['Potassium'] = (3400, None)         # mg
        ranges['Sodium'] = (0, 2300)               # mg
        ranges['Zinc'] = (11, 40)                  # mg
        ranges['Protein'] = (50, None)             # placeholder; overwritten from weight
        return ranges

    if sex != "female":
        raise ValueError("Pregnancy and lactation settings require sex='female'.")

    if age_years < 14:
        raise ValueError("Pregnancy/lactation should not be used for very young age profiles in this project model.")

    if life_stage == "pregnant":
        ranges['Iron'] = (27, 45)
        ranges['Folate'] = (600, 1000)
        ranges['Vitamin_A'] = (770, 3000)
        ranges['Vitamin_C'] = (85, 2000)
        ranges['B12_Cobalamin'] = (2.6, None)
        ranges['Zinc'] = (11, 40)
        ranges['Omega_3'] = (1.4, None)
        # Optional if tracked in data:
        ranges['Iodine'] = (220, 1100)
        # Practical project target:
        ranges['Protein'] = (71, None)
        return ranges

    if life_stage == "lactating":
        ranges['Iron'] = (9, 45)
        ranges['Folate'] = (500, 1000)
        ranges['Vitamin_A'] = (1300, 3000)
        ranges['Vitamin_C'] = (120, 2000)
        ranges['B12_Cobalamin'] = (2.8, None)
        ranges['Zinc'] = (12, 40)
        ranges['Omega_3'] = (1.3, None)
        # Optional if tracked in data:
        ranges['Iodine'] = (290, 1100)
        # Practical project target:
        ranges['Protein'] = (71, None)
        return ranges

    raise ValueError("life_stage must be 'adult', 'pregnant', or 'lactating'")


def apply_energy_based_macros(ranges, energy_kcal):
    """
    Updates fat, saturated fat, and fiber using calorie-based rules.
    """
    # Fiber ~14 g per 1000 kcal
    fiber_min = 14 * energy_kcal / 1000
    ranges['Fiber'] = (fiber_min, 70)

    # Fat 20-35% of kcal
    fat_min = 0.20 * energy_kcal / 9
    fat_max = 0.35 * energy_kcal / 9
    ranges['Fat'] = (fat_min, fat_max)

    # Saturated fat <10% kcal
    sat_fat_max = 0.10 * energy_kcal / 9
    ranges['Saturated_Fat'] = (0, sat_fat_max)

    # Carbs absolute floor
    ranges['Carbs'] = (130, None)

    return ranges


def apply_weight_based_protein(ranges, weight_kg):
    """
    Updates protein minimum using a weight-based rule.
    """
    weight_based_min = 0.8 * weight_kg
    current_min = ranges.get('Protein', (0, None))[0]
    ranges['Protein'] = (max(weight_based_min, current_min), None)
    return ranges


def get_nutrient_ranges(
    sex: str,
    age_years: int,
    weight_kg: float,
    height_cm: float,
    activity_level: str = "moderate",
    goal: str = "maintain",
    life_stage: str = "adult",
):
    """
    Returns a nutrient-ranges dictionary for the optimizer.

    Output format:
        {
            'Protein': (min, max),
            'Vitamin_C': (min, max),
            ...
        }
    """
    sex = sex.lower()
    goal = goal.lower()
    life_stage = life_stage.lower()

    if activity_level not in ACTIVITY_FACTORS:
        raise ValueError(f"activity_level must be one of: {list(ACTIVITY_FACTORS.keys())}")

    ranges = get_base_profile(sex, age_years)

    # Estimate energy
    energy = estimate_energy_kcal(sex, age_years, weight_kg, height_cm, activity_level)

    # Life-stage energy adjustments
    if life_stage == "pregnant":
        energy += 300
    elif life_stage == "lactating":
        energy += 400

    # Goal adjustments
    if goal == "lose":
        energy *= 0.85
    elif goal == "gain":
        energy *= 1.10
    elif goal != "maintain":
        raise ValueError("goal must be 'maintain', 'lose', or 'gain'")

    ranges['Energy'] = (0.9 * energy, 1.1 * energy)

    ranges = apply_energy_based_macros(ranges, energy)
    ranges = apply_weight_based_protein(ranges, weight_kg)
    ranges = apply_life_stage_overrides(ranges, sex, age_years, life_stage)

    return ranges