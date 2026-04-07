import pandas as pd
import constraints as cons
from pulp import HiGHS, LpProblem, LpMaximize, LpVariable, lpSum, LpStatus, LpInteger, LpContinuous, LpBinary
import random

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
foods = foods[~foods['Name'].str.contains('coffee|tea|soda|diet|energy drink|\bwater\b|soft drink|sugar substitute', case=False, na=False)] 
foods = foods.reset_index(drop=True)

# Define keywords for food groups we want to limit to 1 item per day (e.g., only one type of egg, one type of yogurt, etc.)
keywords_to_limit = ['Egg', 'Yogurt', 'Milk', 'Cheese', 'Fish', 'Chicken', 'Beef', 'Pork', 'Tofu', 'Tempeh', 'Lentil', 'Bean', 'Nut', 'Seed']

food_indices = foods.index.tolist()

# Intialize the Problem
prob = LpProblem("Meal_Plan_Optimization", LpMaximize)

# Clean the Name column: Remove hidden characters and extra spaces
foods['Name'] = foods['Name'].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()

user_input = input("Enter a food you want to eat: ").strip()

# 1. Split the input into individual words (e.g., "chicken rice" -> ["chicken", "rice"])
keywords = user_input.split()

# 2. Create a "Mask" that starts as all True
# We will narrow it down by checking every keyword
mask = foods['Name'].notna() # Start with everything

for word in keywords:
    # Update the mask: it must stay True AND contain the current word
    # regex=False prevents errors if the user types special characters like () or []
    mask &= foods['Name'].astype(str).str.contains(word, case=False, na=False, regex=False)

matches = foods[mask]

forced_food_index = None

if not matches.empty:
    print("Matching foods:")
    for idx, row in matches.iterrows():
        print(f"{idx}: {row['Name']}")

    selected_id = input("\nEnter the ID number you want (or press Enter for the first one): ")
    forced_food_index = int(selected_id) if selected_id else matches.index[0]
    print(f"Forcing inclusion of: {foods.at[forced_food_index, 'Name']}")
else:
    print("No matching foods found. Proceeding without forcing any food.")

# Create variables dynamically based on Optimization type column
food_vars = {}
bin_vars = {}
# We loop through each day and each food item, creating a variable for the amount of that food and a binary variable to indicate whether that food is included in the meal plan for that day.
for row in foods[['OptimizationType']].itertuples(index=True):
    i = row.Index
    # use the index or a unique ID for the variable name
    var_name = f"food_{i}"
    bin_name = f"bin_{i}"

    # create binary switch
    bin_vars[(i)] = LpVariable(bin_name, cat=LpBinary)

    # if the optimization type is discrete, we want an integer variable (0, 1, 2, etc.) representing number of servings
    if row.OptimizationType == 'Discrete':
        # use integer variable for discrete optimization
        food_vars[(i)] = LpVariable(var_name, lowBound=0, upBound= 5, cat=LpInteger)

    else:
        # these can be continuous variables
        food_vars[(i)] = LpVariable(var_name, lowBound=0, upBound=5,cat=LpContinuous)
    
    # Add constraint to link binary variable with food variable
    prob += food_vars[(i)] <= 5 * bin_vars[(i)], f"Link_{i}_upper"
    prob += food_vars[(i)] >= 0.1 * bin_vars[(i)], f"Link_{i}_lower"

if forced_food_index is not None:
    prob += bin_vars[forced_food_index] == 1, f"Force_{forced_food_index}"
    prob += food_vars[forced_food_index] >= 1, f"Force_amount_{forced_food_index}"

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

for word, group_indices in keyword_groups.items():
    # the sum of switches for all foods in this group must be <= 1
    # this prevents the solver from picking multiple versions of eggs
    prob += lpSum([bin_vars[(i)] for i in group_indices]) <= 1, f"Limit_{word}"

# define objective function 
prob += lpSum([food_vars[(i)] * foods.at[i, 'satiety_score'] for i in food_indices])


for nutrient in valid_nutrients:
    if nutrient in name_map:
        # Get the column name for this nutrient and the corresponding nutrient values for all foods
        col = name_map[nutrient]
        # Create a dictionary mapping food indices to their nutrient values for this nutrient
        food_data_dict = nutrient_values[col]
        # Create the sum of (food variable * nutrient value) for all foods
        nutrient_sum = lpSum([food_vars[(i)] * food_data_dict[i] for i in food_indices])
        
        # Get the lower and upper bounds for this nutrient from the constraints
        lower_bound, upper_bound = cons.nutrient_ranges[nutrient]
        # Add some random jitter to the nutrient constraints to encourage variety in the meal plans

        # Add constraints for this nutrient
        prob += nutrient_sum >= lower_bound, f"{nutrient}_min_"
        prob += nutrient_sum <= upper_bound, f"{nutrient}_max_"


# solve problem
prob.solve(HiGHS(msg=False))

# output the meal plan
if LpStatus[prob.status] == 'Optimal':
    # Loop through the foods and check which ones were selected for this day (i.e., which food variables have a value greater than 0)
    for i, optimization_type, name, portion_size in foods[['OptimizationType', 'Name', 'Portion size (g)']].itertuples(index=True, name=None):
        value = food_vars[(i)].varValue
        # If the value is None or zero, we skip it (i.e., this food is not included in the meal plan for this day)
        if not value or value <= 0:
            continue

        if food_vars[(i)].cat == LpInteger:
            print(f"{int(value)} serving(s) of {name}")
        else:
            print(f"{value * portion_size} grams of {name}")
else:
    print(f"No optimal solution found. Solver status: {LpStatus[prob.status]}")