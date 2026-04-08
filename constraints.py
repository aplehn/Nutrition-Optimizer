# Default nutrient ranges
# Quantities provided by copilot, TODO: check sources
# Minimum values are based on RDA for adults, maximum values are based on UL where available
nutrient_ranges = {
    'Energy': (2000, 2500), # kcal
    'B6_Pyridoxine': (1.3, 100), # mg
    'B12_Cobalamin': (2.4, None), # mcg
    'Folate': (400, 1000), # mcg
    'Vitamin_A': (900, 3000), # mcg 700 for women, 900 for men, consider user prompt
    'Vitamin_C': (90, 2000), # mg 75 mg women 90 mg men
    'Vitamin_D': (15, 100), # mcg
    'Vitamin_E': (15, 1000), # mg
    'Vitamin_K': (120, None), # mcg 120 mcg men, 90 mcg women
    'Iron': (18, 45), # mg 8 mg men, 18 mg women
    'Carbs': (130, None), # g
    'Fiber': (25, 70), # g
    #'Sugars': (0, 50), # g unnecessary
    'Fat': (44, 77), # g CONSIDER REMOVING, CHECK RESULTS
    # 'Cholesterol': (0, 300), # mg unnecessary, no link between dietary cholesterol and blood cholesterol for most people
    # "Monounsaturated_Fat": (0, 20), # g
    # "Polyunsaturated_Fat": (0, 20), # g
    "Saturated_Fat": (0, 20), # g
    "Omega_3": (1.6, None), # g 1.6 g men 1.1 g women
    # "Omega_6": (0, 20), # g unnecessary
# causes infeasibility in current data set
    'Calcium': (1000, 2500), # mg
    # 'Copper': (900, 1000), # mcg
    'Magnesium': (420, None), # mg 400–420 mg men 310–320 mg women
    # 'Manganese': (2.3, 11), # mg
    # 'Phosphorus': (700, 4000), # mg
    'Potassium': (3400, None), # mg 3400 mg men, 2600 mg women
    # 'Selenium': (55, 400), # mcg
    'Sodium': (1500, 2300), # mg
    # 'Zinc': (11, 40), # mg
    'Protein': (50, None), # g
# current data is missing these 
    # 'B1_Thiamine': (1.1, 1.2), # mg
    # 'B2_Riboflavin': (1.1, 1.3), # mg
    # 'B3_Niacin': (14, 16), # mg
    # 'B5_Pantothenic_Acid': (5, 6), # mg
    # 'B7_Biotin': (30, 100), # mcg
    # 'Starch': (0, 300), # g
    # 'Added_Sugars': (0, 25), # g
    # 'Net_Carbs': (0, 300), # g
    # "Trans_Fat": (0, 2), # g
    # 'Cystine': (0, 5), # g
    # 'Histidine': (0, 5), # g
    # 'Isoleucine': (0, 5), # g
    # 'Leucine': (0, 5), # g
    # 'Lysine': (0, 5), # g
    # 'Methionine': (0, 5), # g
    # 'Phenylalanine': (0, 5), # g
    # 'Protein': (50, 175), # g
    # 'Threonine': (0, 5), # g
    # 'Tryptophan': (0, 5), # g
    # 'Tyrosine': (0, 5), # g
    # 'Valine': (0, 5), # g
}



# Import cronometer csv for dietary data on user decisions for day
import csv
with open('dailysummary.csv') as csv_file:
    csv_read=csv.reader(csv_file, delimiter=',')

