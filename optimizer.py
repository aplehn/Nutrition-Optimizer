import pandas as pd
import constraints as cons
from pulp import HiGHS, LpProblem, LpMaximize, LpVariable, lpSum, LpStatus, LpInteger, LpContinuous, LpBinary
import random
# Maps cons.nutrient_ranges keys -> CSV Column Names
name_map = {
    'Energy': 'Calories (kcal)',
    'Protein': 'Protein (g)',
    'Fat': 'Total Fat (g)',
    'Carbs': 'Carbs (g)',
    'Fiber': 'Fiber (g)',
    'B1_Thiamine': 'Vitamin B-1 (mg)',
    'B2_Riboflavin': 'Vitamin B-2 (mg)',
    'B3_Niacin': 'Vitamin B-3 (mg)',
    'B5_Pantothenic_Acid': 'Vitamin B-5 (mg)',
    'B6_Pyridoxine': 'Vitamin B-6 (mg)',
    'B7_Biotin': 'Vitamin B-7 (mcg)',
    'B12_Cobalamin': 'Vitamin B-12 (mcg)',
    'Folate': 'Folate (mcg)',
    'Vitamin_A': 'Vitamin A (mcg)',
    'Vitamin_C': 'Vitamin C (mg)',
    'Vitamin_D': 'Vitamin D (mcg)',
    'Vitamin_E': 'Vitamin E (mg)',
    'Vitamin_K': 'Vitamin K (mcg)',
    'Calcium': 'Calcium (mg)',
    'Copper': 'Copper (mg)',
    'Iron': 'Iron (mg)',
    'Magnesium': 'Magnesium (mg)',
    'Manganese': 'Manganese (mg)',
    'Phosphorus': 'Phosphorus (mg)',
    'Potassium': 'Potassium (mg)',
    'Selenium': 'Selenium (mcg)',
    'Sodium': 'Sodium (mg)',
    'Zinc': 'Zinc (mg)',
    'Saturated_Fat': 'Saturated Fat (g)',
    'Trans_Fat': 'Trans Fat (g)',
    'Monounsaturated_Fat': 'Monounsaturated Fat (g)',
    'Polyunsaturated_Fat': 'Polyunsaturated Fat (g)',
    'Sugars': 'Sugars (g)',
    'Cholesterol': 'Cholesterol (mg)',
    'Starch': 'Starch (g)',
    'Omega_3': 'Omega-3 EPA (g)',
    'Omega_6': 'Omega-6 (g)',
    
}

# Only keep nutrients that are in both cons.nutrient_ranges and name_map
valid_nutrients = [k for k in cons.nutrient_ranges.keys() if k in name_map]

foods = pd.read_csv('FoodData_with_Optimization_Types.csv')
foods = foods.fillna(0)  # Fill missing nutrient values with 0

# Remove beverages (coffee, tea, soda, diet drinks, energy drinks, water) - these tend to have very low satiety scores and can skew the optimization
beverage_pattern = r'\b(?:coffee|tea|soda|diet|water|energy drink|soft drink|sugar substitute)\b'
foods = foods[~foods['Name'].str.contains(beverage_pattern, case=False, na=False)] 
foods = foods.reset_index(drop=True)

# Define keywords for food groups we want to limit to 1 item per day (e.g., only one type of egg, one type of yogurt, etc.)
keywords_to_limit = ['Egg', 'Yogurt', 'Milk', 'Cheese', 'Fish', 'Chicken', 'Beef', 'Pork', 'Tofu', 'Tempeh', 'Lentil', 'Bean', 'Nut', 'Seed']

food_indices = foods.index.tolist()

# Intialize the Problem
prob = LpProblem("Meal_Plan_Optimization", LpMaximize)

# creating variety in different meal plans
num_days = 3

# Create variables dynamically based on Optimization type column
food_vars = {}
bin_vars = {}
# We loop through each day and each food item, creating a variable for the amount of that food and a binary variable to indicate whether that food is included in the meal plan for that day.
for day in range(num_days):
    for row in foods[['OptimizationType']].itertuples(index=True):
        i = row.Index
        # use the index or a unique ID for the variable name
        var_name = f"food_{day}_{i}"
        bin_name = f"bin_{day}_{i}"

        # create binary switch
        bin_vars[(day, i)] = LpVariable(bin_name, cat=LpBinary)

        # if the optimization type is discrete, we want an integer variable (0, 1, 2, etc.) representing number of servings
        if row.OptimizationType == 'Discrete':
            # use integer variable for discrete optimization
            food_vars[(day, i)] = LpVariable(var_name, lowBound=0, upBound= 5, cat=LpInteger)

        else:
            # these can be continuous variables
            food_vars[(day, i)] = LpVariable(var_name, lowBound=0, upBound=5,cat=LpContinuous)
        
        # Add constraint to link binary variable with food variable
        prob += food_vars[(day, i)] <= 5 * bin_vars[(day, i)], f"Link_{day}_{i}_upper"

# objective function
foods['e_density'] = foods['Calories (kcal)'] / foods['Portion size (g)'].replace(0, 100)
foods['satiety_score'] = (0.5 * foods['Protein (g)']) + (0.3 * foods['Fiber (g)']) - (0.2 * foods['e_density'])

# Group foods by keywords and add constraints to limit the number of similar items (e.g., only one type of egg, one type of yogurt, etc.)
keyword_groups = {}
food_names = foods['Name'].astype(str)
# For each keyword, find the indices of foods that contain that keyword and store them in a dictionary. 
# We will use this to add constraints later to limit the number of items from each group.
for word in keywords_to_limit:
    matching_indices = food_names[food_names.str.contains(word, case=False, na=False)].index.tolist()
    if matching_indices:
        keyword_groups[word] = matching_indices

# Pre-extract nutrient values for valid nutrients to speed up constraint creation
nutrient_values = {name_map[nutrient]: foods[name_map[nutrient]].to_dict() for nutrient in valid_nutrients}

for day in range(num_days):
    for word, group_indices in keyword_groups.items():
        # the sum of switches for all foods in this group must be <= 1
        # this prevents the solver from picking multiple versions of eggs
        prob += lpSum([bin_vars[(day, i)] for i in group_indices]) <= 1, f"Limit_{word}_day_{day}"

# define objective function 
prob += lpSum([food_vars[(day, i)] * foods.at[i, 'satiety_score'] for day in range(num_days) for i in food_indices])

# Add nutrient constraints for each day and each nutrient
for day in range(num_days):
    # randomizes the target
    day_adj = random.uniform(0.98, 1.02)

    # Loop through each valid nutrient and add constraints based on the nutrient values in the foods DataFrame
    for nutrient in valid_nutrients:
        if nutrient in name_map:
            # Get the column name for this nutrient and the corresponding nutrient values for all foods
            col = name_map[nutrient]
            # Create a dictionary mapping food indices to their nutrient values for this nutrient
            food_data_dict = nutrient_values[col]
            # Create the sum of (food variable * nutrient value) for all foods
            nutrient_sum = lpSum([food_vars[(day, i)] * food_data_dict[i] for i in food_indices])
            
            # Get the lower and upper bounds for this nutrient from the constraints
            lower_bound, upper_bound = cons.nutrient_ranges[nutrient]
            # Add some random jitter to the nutrient constraints to encourage variety in the meal plans
            nutri_adj = random.uniform(0.95, 1.05)

            # Calculate the relaxed bounds with the random adjustments
            relaxed_low = lower_bound * nutri_adj * day_adj
            relaxed_high = upper_bound * nutri_adj * day_adj
            # Add constraints for this nutrient
            prob += nutrient_sum >= relaxed_low, f"{nutrient}_min_day_{day}"
            prob += nutrient_sum <= relaxed_high, f"{nutrient}_max_day_{day}"


# If we are optimizing for multiple days, we want to add constraints to ensure variety across days
if num_days > 1:
    for i in food_indices:
        prob += lpSum([bin_vars[(day, i)] for day in range(num_days)]) <= 1, f"Limit_{i}_appearances"

# solve problem
prob.solve(HiGHS(msg=False))

# output the meal plan
if LpStatus[prob.status] == 'Optimal':
    for day in range(num_days):
        print(f"\n--- Day {day + 1} ---")
        # Loop through the foods and check which ones were selected for this day (i.e., which food variables have a value greater than 0)
        for i, optimization_type, name, portion_size in foods[['OptimizationType', 'Name', 'Portion size (g)']].itertuples(index=True, name=None):
            value = food_vars[(day, i)].varValue
            # If the value is None or zero, we skip it (i.e., this food is not included in the meal plan for this day)
            if not value or value <= 0:
                continue

            if optimization_type == 'Discrete':
                print(f"{int(value)} serving(s) of {name}")
            else:
                print(f"{value * portion_size} grams of {name}")
else:
    print(f"No optimal solution found. Solver status: {LpStatus[prob.status]}")


# def calculate_satiety(row):
#     # a=0.5, b=0.3, c=0.2 based on your logic
#     # Energy density = kcal / 100g

#     # will need to adjust grams based on serving size in the future, but for now we can just use kcal as a proxy for energy density
#     e_density = row['Calories (kcal)'] / (row['Portion size (g)'] if row['Portion size (g)'] > 0 else 100) # Avoid division by zero
#     score = (0.5 * row['Protein (g)']) + (0.3 * row['Fiber (g)']) - (0.2 * e_density)
#     return -score # Negative because milp minimizes

# # Calculate the satiety score for each food and use it as the objective function (c)
# c = foods.apply(calculate_satiety, axis=1).values
# print("Objective function (satiety scores):", c)

# # 1. Define Integrality (1 means the variable MUST be an integer)
# # If you have 10 foods, you need a list of ten 1s.
# # This tells the optimizer that you can only eat whole servings of each food (no fractions).
# integrality = np.ones(len(foods))

# # 2. Set bounds (e.g., you can eat 0 to 5 servings of any food)
# bounds = Bounds(0, 10)

# # 3. Define Constraints (A_ub and b_ub from before)
# # SciPy MILP uses LinearConstraint objects
# cols = list(cons.nutrient_ranges.keys())
# A_ub = foods[[name_map[k] for k in valid_nutrients]].fillna(0).values.T
# lb = np.array([cons.nutrient_ranges[k][0] for k in valid_nutrients], dtype=float)
# ub = np.array([cons.nutrient_ranges[k][1] for k in valid_nutrients], dtype=float)
# constraints = LinearConstraint(A_ub, lb, ub)

# integrality = np.ones(len(foods))
# constraints = LinearConstraint(A_ub, lb, ub)

# # 4. Solve
# res = milp(c=c, constraints=constraints, bounds=bounds)

# if res.success:
#     # print("Optimized Meal Plan:", res.x)
#     # for i, servings in enumerate(res.x):
#     #     if servings > 0:
#     #         print(f"{foods['Name'][i]}: {servings:.2f} servings")
#     print("\n--- Optimized Meal Plan ---")
#     # Identify which foods were selected (servings > 0)
#     selected_indices = np.where(res.x > 0.01)[0] # Using 0.01 to avoid floating point noise
    
#     for i in selected_indices:
#         print(f"{foods['Name'].iloc[i]}: {res.x[i]:.2f} servings")

#     print("\n--- Nutritional Totals ---")
#     # Matrix multiplication: Servings (1 x Foods) @ Nutrient Data (Foods x Nutrients)
#     # result_totals will be an array of totals for each nutrient in 'valid_nutrients'
#     nutrient_values = foods[[name_map[k] for k in valid_nutrients]].values # Extract the nutrient values for the valid nutrients
#     totals = res.x @ nutrient_values # This gives us the total amount of each nutrient in the optimized meal plan

#     for idx, nutrient_key in enumerate(valid_nutrients): # Loop through the valid nutrients
#         current_total = totals[idx] # Total amount of this nutrient in the optimized meal plan
#         lower_bound = cons.nutrient_ranges[nutrient_key][0] # Minimum required amount for this nutrient
#         upper_bound = cons.nutrient_ranges[nutrient_key][1] # Maximum allowed amount for this nutrient
        
#         # Print the nutrient name, the calculated total, and the target range
#         print(f"{name_map[nutrient_key]:<25}: {current_total:>8.2f} (Target: {lower_bound}-{upper_bound})")
# else:
#     print("Optimization failed:", res.message)




# num_meals = 7

# print(f"Finding {num_meals} meal plans...\n")

# for i in range(num_meals):
#     # 1. Create a random "multiplier" for every food item
#     # This creates an array of numbers like [1.02, 0.98, 1.01...]
#     jitter = np.random.uniform(0.95, 1.05, size=len(c))
    
#     # 2. Apply it to your original satiety scores (c)
#     jittered_c = c * jitter
    
#     # 3. Solve the MILP with the slightly altered scores
#     res = milp(c=jittered_c, constraints=constraints, bounds=bounds)
    
#     if res.success:
#         print(f"\n--- Meal Plan {i+1} ---")
#         # Identify which foods were selected (servings > 0)
#         selected_indices = np.where(res.x > 0.01)[0] # Using 0.01 to avoid floating point noise
#         for j in selected_indices:
#             print(f"{foods['Name'].iloc[j]}: {res.x[j]:.2f} servings") # Print the name of the food and how many servings
        
#         print("\n--- Nutritional Totals ---")
#         nutrient_values = foods[[name_map[k] for k in valid_nutrients]].values # Extract the nutrient values for the valid nutrients
#         totals = res.x @ nutrient_values # This gives us the total amount of each nutrient in the optimized meal plan

#         for idx, nutrient_key in enumerate(valid_nutrients): # Loop through the valid nutrients
#             current_total = totals[idx] # Total amount of this nutrient in the optimized meal plan
#             lower_bound = cons.nutrient_ranges[nutrient_key][0] # Minimum required amount for this nutrient
#             upper_bound = cons.nutrient_ranges[nutrient_key][1] # Maximum allowed amount for this nutrient
            
#             # Print the nutrient name, the calculated total, and the target range
#             print(f"{name_map[nutrient_key]:<25}: {current_total:>8.2f} (Target: {lower_bound}-{upper_bound})")
#     else:
#         print("Optimization failed:", res.message)




# Name,Type,FDC ID,Protein (g),Total Fat (g),Carbs (g),Calories (kcal),Sugars (g),Fiber (g),Calcium (mg),Iron (mg),Magnesium (mg),
# Phosphorus (mg),Potassium (mg),Sodium (mg),Zinc (mg),Copper (mg),Selenium (mcg),Vitamin A (mcg),Vitamin E (mg),Vitamin D (mcg),
# Vitamin C (mg),Vitamin B-1 (mg),Vitamin B-2 (mg),Vitamin B-3 (mg),Vitamin B-6 (mg),Folate (mcg),Vitamin B-12 (mcg),Vitamin K (mcg),
# Cholesterol (mg),Saturated Fat (g),Omega-3 EPA (g),Monounsaturated Fat (g),Polyunsaturated Fat (g)


# {"foodClass":"Survey","description":"Soy milk, chocolate",
# "foodNutrients":[{"type":"FoodNutrient","id":34137589,
# "nutrient":{"id":1003,"number":"203","name":"Protein","rank":600,"unitName":"g"},"amount":3.35},{"type":"FoodNutrient","id":34137590,
# "nutrient":{"id":1004,"number":"204","name":"Total lipid (fat)","rank":800,"unitName":"g"},"amount":2.03},{"type":"FoodNutrient","id":34137591,
# "nutrient":{"id":1005,"number":"205","name":"Carbohydrate, by difference","rank":1110,"unitName":"g"},"amount":8.32},{"type":"FoodNutrient","id":34137592,
# "nutrient":{"id":1008,"number":"208","name":"Energy","rank":300,"unitName":"kcal"},"amount":64.0},{"type":"FoodNutrient","id":34137593,
# "nutrient":{"id":1018,"number":"221","name":"Alcohol, ethyl","rank":18200,"unitName":"g"},"amount":0.000},{"type":"FoodNutrient","id":34137594,
# "nutrient":{"id":1051,"number":"255","name":"Water","rank":100,"unitName":"g"},"amount":85.7},{"type":"FoodNutrient","id":34137595,
# "nutrient":{"id":1057,"number":"262","name":"Caffeine","rank":18300,"unitName":"mg"},"amount":1.00},{"type":"FoodNutrient","id":34137596,
# "nutrient":{"id":1058,"number":"263","name":"Theobromine","rank":18400,"unitName":"mg"},"amount":6.00},{"type":"FoodNutrient","id":34137597,
# "nutrient":{"id":2000,"number":"269","name":"Total Sugars","rank":1510,"unitName":"g"},"amount":7.49},{"type":"FoodNutrient","id":34137598,
# "nutrient":{"id":1079,"number":"291","name":"Fiber, total dietary","rank":1200,"unitName":"g"},"amount":0.100},{"type":"FoodNutrient","id":34137599,
# "nutrient":{"id":1087,"number":"301","name":"Calcium, Ca","rank":5300,"unitName":"mg"},"amount":94.0},{"type":"FoodNutrient","id":34137600,
# "nutrient":{"id":1089,"number":"303","name":"Iron, Fe","rank":5400,"unitName":"mg"},"amount":0.550},{"type":"FoodNutrient","id":34137601,
# "nutrient":{"id":1090,"number":"304","name":"Magnesium, Mg","rank":5500,"unitName":"mg"},"amount":22.0},{"type":"FoodNutrient","id":34137602,
# "nutrient":{"id":1091,"number":"305","name":"Phosphorus, P","rank":5600,"unitName":"mg"},"amount":66.0},{"type":"FoodNutrient","id":34137603,
# "nutrient":{"id":1092,"number":"306","name":"Potassium, K","rank":5700,"unitName":"mg"},"amount":151},{"type":"FoodNutrient","id":34137604,
# "nutrient":{"id":1093,"number":"307","name":"Sodium, Na","rank":5800,"unitName":"mg"},"amount":32.0},{"type":"FoodNutrient","id":34137605,
# "nutrient":{"id":1095,"number":"309","name":"Zinc, Zn","rank":5900,"unitName":"mg"},"amount":0.310},{"type":"FoodNutrient","id":34137606,
# "nutrient":{"id":1098,"number":"312","name":"Copper, Cu","rank":6000,"unitName":"mg"},"amount":0.112},{"type":"FoodNutrient","id":34137607,
# "nutrient":{"id":1103,"number":"317","name":"Selenium, Se","rank":6200,"unitName":"µg"},"amount":1.80},{"type":"FoodNutrient","id":34137608,
# "nutrient":{"id":1105,"number":"319","name":"Retinol","rank":7430,"unitName":"µg"},"amount":54.0},{"type":"FoodNutrient","id":34137609,
# "nutrient":{"id":1106,"number":"320","name":"Vitamin A, RAE","rank":7420,"unitName":"µg"},"amount":54.0},{"type":"FoodNutrient","id":34137610,
# "nutrient":{"id":1107,"number":"321","name":"Carotene, beta","rank":7440,"unitName":"µg"},"amount":0.000},{"type":"FoodNutrient","id":34137611,
# "nutrient":{"id":1108,"number":"322","name":"Carotene, alpha","rank":7450,"unitName":"µg"},"amount":0.000},{"type":"FoodNutrient","id":34137612,
# "nutrient":{"id":1109,"number":"323","name":"Vitamin E (alpha-tocopherol)","rank":7905,"unitName":"mg"},"amount":0.150},{"type":"FoodNutrient","id":34137613,
# "nutrient":{"id":1114,"number":"328","name":"Vitamin D (D2 + D3)","rank":8700,"unitName":"µg"},"amount":0.600},{"type":"FoodNutrient","id":34137614,
# "nutrient":{"id":1120,"number":"334","name":"Cryptoxanthin, beta","rank":7460,"unitName":"µg"},"amount":0.000},{"type":"FoodNutrient","id":34137615,'
# "nutrient":{"id":1122,"number":"337","name":"Lycopene","rank":7530,"unitName":"µg"},"amount":0.000},{"type":"FoodNutrient","id":34137616,
# "nutrient":{"id":1123,"number":"338","name":"Lutein + zeaxanthin","rank":7560,"unitName":"µg"},"amount":8.00},{"type":"FoodNutrient","id":34137617,
# "nutrient":{"id":1162,"number":"401","name":"Vitamin C, total ascorbic acid","rank":6300,"unitName":"mg"},"amount":0.000},{"type":"FoodNutrient","id":34137618,
# "nutrient":{"id":1165,"number":"404","name":"Thiamin","rank":6400,"unitName":"mg"},"amount":0.059},{"type":"FoodNutrient","id":34137619,
# "nutrient":{"id":1166,"number":"405","name":"Riboflavin","rank":6500,"unitName":"mg"},"amount":0.080},{"type":"FoodNutrient","id":34137620,
# "nutrient":{"id":1167,"number":"406","name":"Niacin","rank":6600,"unitName":"mg"},"amount":0.225},{"type":"FoodNutrient","id":34137621,
# "nutrient":{"id":1175,"number":"415","name":"Vitamin B-6","rank":6800,"unitName":"mg"},"amount":0.051},{"type":"FoodNutrient","id":34137622,
# "nutrient":{"id":1177,"number":"417","name":"Folate, total","rank":6900,"unitName":"µg"},"amount":19.0},{"type":"FoodNutrient","id":34137623,
# "nutrient":{"id":1178,"number":"418","name":"Vitamin B-12","rank":7300,"unitName":"µg"},"amount":0.360},{"type":"FoodNutrient","id":34137624,
# "nutrient":{"id":1180,"number":"421","name":"Choline, total","rank":7220,"unitName":"mg"},"amount":21.9},{"type":"FoodNutrient","id":34137625,
# "nutrient":{"id":1185,"number":"430","name":"Vitamin K (phylloquinone)","rank":8800,"unitName":"µg"},"amount":2.80},{"type":"FoodNutrient","id":34137626,
# "nutrient":{"id":1186,"number":"431","name":"Folic acid","rank":7000,"unitName":"µg"},"amount":0.000},{"type":"FoodNutrient","id":34137627,
# "nutrient":{"id":1187,"number":"432","name":"Folate, food","rank":7100,"unitName":"µg"},"amount":19.0},{"type":"FoodNutrient","id":34137628,
# "nutrient":{"id":1190,"number":"435","name":"Folate, DFE","rank":7200,"unitName":"µg"},"amount":19.0},{"type":"FoodNutrient","id":34137629,
# "nutrient":{"id":1242,"number":"573","name":"Vitamin E, added","rank":7920,"unitName":"mg"},"amount":0.000},{"type":"FoodNutrient","id":34137630,
# "nutrient":{"id":1246,"number":"578","name":"Vitamin B-12, added","rank":7340,"unitName":"µg"},"amount":0.360},{"type":"FoodNutrient","id":34137631,
# "nutrient":{"id":1253,"number":"601","name":"Cholesterol","rank":15700,"unitName":"mg"},"amount":0.000},{"type":"FoodNutrient","id":34137632,
# "nutrient":{"id":1258,"number":"606","name":"Fatty acids, total saturated","rank":9700,"unitName":"g"},"amount":0.315},{"type":"FoodNutrient","id":34137633,
# "nutrient":{"id":1259,"number":"607","name":"SFA 4:0","rank":9800,"unitName":"g"},"amount":0.000},{"type":"FoodNutrient","id":34137634,
# "nutrient":{"id":1260,"number":"608","name":"SFA 6:0","rank":9900,"unitName":"g"},"amount":0.000},{"type":"FoodNutrient","id":34137635,
# "nutrient":{"id":1261,"number":"609","name":"SFA 8:0","rank":10000,"unitName":"g"},"amount":0.000},{"type":"FoodNutrient","id":34137636,
# "nutrient":{"id":1262,"number":"610","name":"SFA 10:0","rank":10100,"unitName":"g"},"amount":0.000},{"type":"FoodNutrient","id":34137637,
# "nutrient":{"id":1263,"number":"611","name":"SFA 12:0","rank":10300,"unitName":"g"},"amount":0.000},{"type":"FoodNutrient","id":34137638,
# "nutrient":{"id":1264,"number":"612","name":"SFA 14:0","rank":10500,"unitName":"g"},"amount":0.004},{"type":"FoodNutrient","id":34137639,
# "nutrient":{"id":1265,"number":"613","name":"SFA 16:0","rank":10700,"unitName":"g"},"amount":0.213},{"type":"FoodNutrient","id":34137640,
# "nutrient":{"id":1266,"number":"614","name":"SFA 18:0","rank":10900,"unitName":"g"},"amount":0.080},{"type":"FoodNutrient","id":34137641,
# "nutrient":{"id":1268,"number":"617","name":"MUFA 18:1","rank":12100,"unitName":"g"},"amount":0.394},{"type":"FoodNutrient","id":34137642,
# "nutrient":{"id":1269,"number":"618","name":"PUFA 18:2","rank":13100,"unitName":"g"},"amount":0.918},{"type":"FoodNutrient","id":34137643,'
# "nutrient":{"id":1270,"number":"619","name":"PUFA 18:3","rank":13900,"unitName":"g"},"amount":0.154},{"type":"FoodNutrient","id":34137644,
# "nutrient":{"id":1271,"number":"620","name":"PUFA 20:4","rank":14700,"unitName":"g"},"amount":0.000},{"type":"FoodNutrient","id":34137645,
# "nutrient":{"id":1272,"number":"621","name":"PUFA 22:6 n-3 (DHA)","rank":15300,"unitName":"g"},"amount":0.000},{"type":"FoodNutrient","id":34137646,
# "nutrient":{"id":1275,"number":"626","name":"MUFA 16:1","rank":11700,"unitName":"g"},"amount":0.002},{"type":"FoodNutrient","id":34137647,
# "nutrient":{"id":1276,"number":"627","name":"PUFA 18:4","rank":14250,"unitName":"g"},"amount":0.000},{"type":"FoodNutrient","id":34137648,
# "nutrient":{"id":1277,"number":"628","name":"MUFA 20:1","rank":12400,"unitName":"g"},"amount":0.005},{"type":"FoodNutrient","id":34137649,
# "nutrient":{"id":1278,"number":"629","name":"PUFA 20:5 n-3 (EPA)","rank":15000,"unitName":"g"},"amount":0.000},{"type":"FoodNutrient","id":34137650,
# "nutrient":{"id":1279,"number":"630","name":"MUFA 22:1","rank":12500,"unitName":"g"},"amount":0.000},{"type":"FoodNutrient","id":34137651,
# "nutrient":{"id":1280,"number":"631","name":"PUFA 22:5 n-3 (DPA)","rank":15200,"unitName":"g"},"amount":0.000},{"type":"FoodNutrient","id":34137652,
# "nutrient":{"id":1292,"number":"645","name":"Fatty acids, total monounsaturated","rank":11400,"unitName":"g"},"amount":0.399},{"type":"FoodNutrient","id":34137653,
# "nutrient":{"id":1293,"number":"646","name":"Fatty acids, total polyunsaturated","rank":12900,"unitName":"g"},"amount":1.07}],"foodAttributes":[{"id":3318846,"value":"Moisture change: 0%","foodAttributeType":{"id":1002,"name":"Adjustments","description":"Adjustments made to foods, including moisture changes"}},{"id":3298360,"name":"WWEIA Category description","value":"Plant-based milk","foodAttributeType":{"id":999,"name":"Attribute","description":"Generic attributes"}},{"id":3298359,"name":"WWEIA Category number","value":"1902","foodAttributeType":{"id":999,"name":"Attribute","description":"Generic attributes"}}],"foodCode":"11321000","startDate":"1/1/2021","endDate":"12/31/2023","wweiaFoodCategory":{"wweiaFoodCategoryDescription":"Plant-based milk","wweiaFoodCategoryCode":3298360},"dataType":"Survey (FNDDS)","fdcId":2705406,"foodPortions":[{"id":290619,"measureUnit":{"id":9999,"name":"undetermined","abbreviation":"undetermined"},"modifier":"90000","gramWeight":244,"portionDescription":"Quantity not specified","sequenceNumber":3},{"id":290617,"measureUnit":{"id":9999,"name":"undetermined","abbreviation":"undetermined"},"modifier":"10205","gramWeight":244,"portionDescription":"1 cup","sequenceNumber":1},{"id":290618,"measureUnit":{"id":9999,"name":"undetermined","abbreviation":"undetermined"},"modifier":"30000","gramWeight":30.5,"portionDescription":"1 fl oz","sequenceNumber":2}],"publicationDate":"10/31/2024","inputFoods":[{"id":124300,"unit":"GM","portionDescription":"NONE","portionCode":"0","foodDescription":"Soy milk, unsweetened, plain, shelf stable","retentionCode":0,"ingredientWeight":93,"ingredientCode":16222,"ingredientDescription":"Soy milk, unsweetened, plain, shelf stable","amount":93,"sequenceNumber":1},{"id":124301,"unit":"GM","portionDescription":"NONE","portionCode":"0","foodDescription":"Sugars, granulated","retentionCode":0,"ingredientWeight":7,"ingredientCode":19335,"ingredientDescription":"Sugars, granulated","amount":7,"sequenceNumber":2},{"id":124302,"unit":"GM","portionDescription":"NONE","portionCode":"0","foodDescription":"Cocoa, dry powder, unsweetened","retentionCode":0,"ingredientWeight":0.299999999999999988897769753748434595763683319091796875,"ingredientCode":19165,"ingredientDescription":"Cocoa, dry powder, unsweetened","amount":0.299999999999999988897769753748434595763683319091796875,"sequenceNumber":3}]},