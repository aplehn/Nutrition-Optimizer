# Default nutrient ranges
# Quantities provided by copilot, TODO: check sources
nutrient_ranges = {
    'Energy': (2000, 2500), # kcal
    # 'B1_Thiamine': (1.1, 1.2), # mg
    # 'B2_Riboflavin': (1.1, 1.3), # mg
    # 'B3_Niacin': (14, 16), # mg
    'B5_Pantothenic_Acid': (5, 6), # mg
    'B6_Pyridoxine': (1.3, 1.7), # mg
    'B7_Biotin': (30, 100), # mcg
    'B12_Cobalamin': (2.4, 2.8), # mcg
    'Folate': (400, 600), # mcg
    'Vitamin_A': (700, 900), # mcg
    'Vitamin_C': (75, 90), # mg
    'Vitamin_D': (15, 20), # mcg
    'Vitamin_E': (15, 20), # mg
    'Vitamin_K': (90, 120), # mcg
    # 'Calcium': (1000, 1300), # mg
    # 'Copper': (900, 1000), # mcg
    'Iron': (8, 18), # mg
    # 'Magnesium': (400, 420), # mg
    # 'Manganese': (2.3, 2.6), # mg
    # 'Phosphorus': (700, 1250), # mg
    # 'Potassium': (4000, 4700), # mg
    # 'Selenium': (55, 70), # mcg
    # 'Sodium': (1500, 2300), # mg
    # 'Zinc': (11, 15), # mg
    'Carbs': (225, 325), # g
    'Fiber': (25, 38), # g
    'Starch': (0, 300), # g
    'Sugars': (0, 50), # g
    'Added_Sugars': (0, 25), # g
    'Net_Carbs': (0, 300), # g
    'Fat': (44, 77), # g
    'Cholesterol': (0, 300), # mg
    "Monounsaturated_Fat": (0, 20), # g
    "Polyunsaturated_Fat": (0, 20), # g
    "Saturated_Fat": (0, 20), # g
    "Trans_Fat": (0, 2), # g
    "Omega_3": (0, 3), # g
    "Omega_6": (0, 20), # g
    'Cystine': (0, 5), # g
    'Histidine': (0, 5), # g
    'Isoleucine': (0, 5), # g
    'Leucine': (0, 5), # g
    'Lysine': (0, 5), # g
    'Methionine': (0, 5), # g
    'Phenylalanine': (0, 5), # g
    'Protein': (50, 175), # g
    'Threonine': (0, 5), # g
    'Tryptophan': (0, 5), # g
    'Tyrosine': (0, 5), # g
    'Valine': (0, 5), # g
}



# Import cronometer csv for dietary data on user decisions for day
import csv
with open('dailysummary.csv') as csv_file:
    csv_read=csv.reader(csv_file, delimiter=',')

