# Import USDA Food Data
import json
import pandas as pd

with open('FoodData_Central_foundation_food_json_2025-12-18.json') as json_file:
    usda_food_data = json.load(json_file)


df = pd.json_normalize(usda_food_data['FoundationFoods'])

df_sorted = df.sort_values(by='description')

# Define the specific nutrients from your list that you want to extract and their corresponding column names in the USDA data
target_nutrients = {
    "Energy": "Energy (kcal)",
    "Protein": "Protein (g)",
    "Total lipid (fat)": "Fat (g)",
    "Carbohydrate, by difference": "Carbs (g)",
    "Cholesterol": "Cholesterol (mg)",
    "Sugars, total including nlea": "Sugars (g)",
    "Vitamin A": "Vitamin A, RAE (Âµg)",
    "Vitamin B-6": "Vitamin B-6 (mg)", 
    "Vitamin B-12": "Vitamin B-12 (Âµg)",
    "Vitamin C": "Vitamin C, total ascorbic acid (mg)",
    "Folate": "Folate, total (Âµg)",
    "Potassium": "Potassium, K (mg)",
    "Magnesium": "Magnesium, Mg (mg)",
    "Calcium": "Calcium, Ca (mg)",
    "Iron": "Iron, Fe (mg)",
    "Sodium": "Sodium, Na (mg)",
    "Fiber": "Fiber, total dietary (g)",
    "Saturated Fat": "Fatty acids, total saturated (g)",
    "Monounsaturated Fat": "Fatty acids, total monounsaturated (g)",
    
}

rows = []
for food in usda_food_data['FoundationFoods']:
    # Basic info
    entry = {
        'Name': food.get('description'),
        'Type': food.get('foodCategory', {}).get('description', 'N/A'),
        'FDC ID': food.get('fdcId')
    }
    
    # Extract only the specific nutrients requested
    nutrients = food.get('foodNutrients', [])
    for n in nutrients:
        n_name = n['nutrient']['name']
        if n_name in target_nutrients:
            column_name = target_nutrients[n_name]
            entry[column_name] = n.get('amount')

    rows.append(entry)

# 3. Create DataFrame
df = pd.DataFrame(rows)

# 4. Sort by Name (Alphabetical) then by Type
df = df.sort_values(by=['Name', 'Type'])

# 5. Save to CSV
df.to_csv('FoodData_Sorted_Filtered.csv', index=False)
print("File saved as FoodData_Sorted_Filtered.csv")



# description,fdcId,category,"Cryptoxanthin, beta (Âµg)",Lycopene (Âµg),"Tocopherol, delta (mg)","Tocotrienol, gamma (mg)",
# "Tocotrienol, delta (mg)","Vitamin C, total ascorbic acid (mg)",Thiamin (mg),Riboflavin (mg),"Folate, total (Âµg)",
# Vitamin K (Dihydrophylloquinone) (Âµg),Vitamin K (phylloquinone) (Âµg),"Fatty acids, total trans (g)","Fatty acids, total saturated (g)",
# SFA 8:0 (g),SFA 12:0 (g),SFA 14:0 (g),PUFA 22:6 n-3 (DHA) (g),SFA 22:0 (g),PUFA 20:5 n-3 (EPA) (g),PUFA 22:5 n-3 (DPA) (g),SFA 17:0 (g),
# SFA 24:0 (g),TFA 16:1 t (g),MUFA 24:1 c (g),MUFA 18:1 c (g),"PUFA 18:2 n-6 c,c (g)",MUFA 22:1 c (g),MUFA 17:1 (g),"Fatty acids, total trans-monoenoic (g)",
# MUFA 15:1 (g),"PUFA 18:3 n-3 c,c,c (ALA) (g)",PUFA 20:3 n-3 (g),PUFA 22:4 (g),Protein (g),Ash (g),Starch (g),Fructose (g),Lactose (g),Energy (kJ),
# Galactose (g),"Fiber, total dietary (g)","Iron, Fe (mg)","Magnesium, Mg (mg)","Phosphorus, P (mg)","Sodium, Na (mg)","Copper, Cu (mg)","Manganese, Mn (mg)",
# "Vitamin A, RAE (Âµg)","Carotene, beta (Âµg)","Carotene, alpha (Âµg)",PUFA 20:4 (g),PUFA 18:4 (g),"Fatty acids, total monounsaturated (g)",
# "Fatty acids, total polyunsaturated (g)",SFA 15:0 (g),TFA 18:1 t (g),TFA 22:1 t (g),TFA 18:2 t not further defined (g),PUFA 18:2 CLAs (g),
# "PUFA 20:2 n-6 c,c (g)",MUFA 16:1 c (g),"PUFA 18:3 n-6 c,c,c (g)","Fatty acids, total trans-polyenoic (g)",PUFA 20:3 n-6 (g),SFA 4:0 (g),
# SFA 6:0 (g),SFA 10:0 (g),SFA 16:0 (g),SFA 18:0 (g),SFA 20:0 (g),Lutein + zeaxanthin (Âµg),"Tocopherol, beta (mg)","Tocopherol, gamma (mg)",
# "Tocotrienol, alpha (mg)","Tocotrienol, beta (mg)",Niacin (mg),Pantothenic acid (mg),Vitamin B-6 (mg),Vitamin K (Menaquinone-4) (Âµg),Total lipid (fat) (g),
# "Carbohydrate, by difference (g)",Energy (kcal),Sucrose (g),Glucose (g),Maltose (g),Water (g),"Calcium, Ca (mg)","Potassium, K (mg)","Zinc, Zn (mg)","Selenium, Se (Âµg)",
# Vitamin E (alpha-tocopherol) (mg),Nitrogen (g),MUFA 14:1 c (g),MUFA 20:1 c (g),MUFA 22:1 n-9 (g),PUFA 22:2 (g),SFA 11:0 (g),TFA 18:3 t (g),PUFA 20:3 n-9 (g),
# "Choline, total (mg)","Choline, from glycerophosphocholine (mg)",Betaine (mg),"Choline, from sphingomyelin (mg)","Choline, free (mg)","Choline, from phosphotidyl choline (mg)",
# "Choline, from phosphocholine (mg)","Sugars, Total (g)","Carbohydrate, by summation (g)","Fatty acids, total trans-dienoic (g)",MUFA 17:1 c (g),PUFA 18:2 c (g),PUFA 18:3 c (g),
# PUFA 20:3 c (g),PUFA 20:4c (g),PUFA 20:5c (g),PUFA 22:5 c (g),PUFA 22:6 c (g),PUFA 20:2 c (g),Total fat (NLEA) (g),"Cryptoxanthin, alpha (Âµg)",trans-beta-Carotene (Âµg),
# cis-beta-Carotene (Âµg),cis-Lutein/Zeaxanthin (Âµg),cis-Lycopene (Âµg),Lutein (Âµg),Zeaxanthin (Âµg),Vitamin A (mg),Vitamin B-12 (Âµg),Retinol (Âµg),Vitamin D2 (ergocalciferol) (Âµg),
# Vitamin D3 (cholecalciferol) (Âµg),Vitamin D (D2 + D3) (Âµg),"Vitamin D (D2 + D3), International Units (IU)",Cholesterol (mg),25-hydroxycholecalciferol (Âµg),"Iodine, I (Âµg)",MUFA 20:1 (g),
# PUFA 18:3i (g),Specific Gravity (sp gr),Tryptophan (g),Threonine (g),Methionine (g),Phenylalanine (g),Tyrosine (g),Alanine (g),Glutamic acid (g),Glycine (g),Proline (g),Isoleucine (g),Leucine (g),
# Lysine (g),Cystine (g),Valine (g),Arginine (g),Histidine (g),Aspartic acid (g),Serine (g),"Fiber, insoluble (g)","Fiber, soluble (g)",Hydroxyproline (g),MUFA 22:1 (g),MUFA 18:1 (g),PUFA 18:2 (g),
# PUFA 18:3 (g),SFA 5:0 (g),SFA 7:0 (g),SFA 9:0 (g),MUFA 12:1 (g),TFA 14:1 t (g),TFA 20:1 t (g),SFA 21:0 (g),MUFA 22:1 n-11 (g),SFA 23:0 (g),PUFA 22:3 (g),Cysteine (g),
# 10-Formyl folic acid (10HCOFA) (Âµg),5-Formyltetrahydrofolic acid (5-HCOH4 (Âµg),5-methyl tetrahydrofolate (5-MTHF) (Âµg),Phytofluene (Âµg),Phytoene (Âµg),trans-Lycopene (Âµg),"Boron, B (Âµg)",
# "Cobalt, Co (Âµg)","Molybdenum, Mo (Âµg)","Nickel, Ni (Âµg)","Sulfur, S (mg)",PUFA 20:3 (g),Biotin (Âµg),Beta-sitosterol (mg),Brassicasterol (mg),Campestanol (mg),Campesterol (mg),
# Delta-5-avenasterol (mg),"Phytosterols, other (mg)",Beta-sitostanol (mg),Stigmasterol (mg),Total dietary fiber (AOAC 2011.25) (g),Citric acid (mg),Malic acid (mg),Total Sugars (g),
# Energy (Atwater General Factors) (kcal),Energy (Atwater Specific Factors) (kcal),Delta-7-Stigmastenol (mg),Stigmastadiene (mg),TFA 18:2 t (g),Ergosterol (mg),Ergothioneine (mg),Vitamin D4 (Âµg),
# Ergosta-7-enol (mg),"Ergosta-7,22-dienol (mg)","Ergosta-5,7-dienol (mg)",Beta-glucan (g),Glutathione (mg),Daidzin (mg),Genistin (mg),Glycitin (mg),Verbascose (g),Raffinose (g),Stachyose (g),
# Daidzein (mg),Genistein (mg),"Carotene, gamma (Âµg)",Oxalic acid (mg),Quinic acid (mg),Low Molecular Weight Dietary Fiber (LMWDF) (g),High Molecular Weight Dietary Fiber (HMWDF) (g),Pyruvic acid (mg),Resistant starch (g)
