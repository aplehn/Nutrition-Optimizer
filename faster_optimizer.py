import pandas as pd
import constraints as cons
from pulp import HiGHS, LpProblem, LpMaximize, LpVariable, lpSum, LpStatus, LpInteger, LpContinuous, LpBinary
import re

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
beverage_pattern = r'\b(?:coffee|tea|soda|diet|water|energy drink|soft drink|sugar substitute|dessert)\b'
foods = foods[~foods['Name'].str.contains(beverage_pattern, case=False, na=False)] 
foods = foods.reset_index(drop=True)

# Define keywords for food groups we want to limit to 1 item per day (e.g., only one type of egg, one type of yogurt, etc.)
keywords_to_limit = ['Egg', 'Yogurt', 'Milk', 'Cheese', 'Fish', 'Chicken', 'Beef', 'Pork', 'Tofu', 'Tempeh', 'Lentil', 'Bean', 'Nut', 'Seed']

food_indices = foods.index.tolist()

# Intialize the Problem
prob = LpProblem("Meal_Plan_Optimization", LpMaximize)

# objective function
foods['e_density'] = foods['Calories (kcal)'] / foods['Portion size (g)'].replace(0, 100)
foods['satiety_score'] = (0.5 * foods['Protein (g)']) + (0.3 * foods['Fiber (g)']) - (0.2 * foods['e_density'])

# --- SEARCH AND SELECTION ---
search_query = input("Enter food you want to eat with meal: ")

# This function uses a regex pattern to check if the food name contains the search query but is not preceded by the word "excluding".
def exclusion_filter(name, query):
    # This regex ensures the query isn't preceded by the word "excluding"
    safe_query = re.escape(query)
    # The pattern looks for the query anywhere in the string, but only if it's not preceded by "excluding" (with any number of characters in between). 
    pattern = rf"^(?!.*excluding.*{safe_query}).*{safe_query}"
    return bool(re.search(pattern, name, re.IGNORECASE)) # This will return True for names that contain the query and are not preceded by "excluding", and False otherwise.

# Apply the clever filter instead of the simple .contains()
matches = foods[foods['Name'].apply(lambda x: exclusion_filter(x, search_query))]

if not matches.empty:
    # Optional: Sort by satiety_score so the best options appear first
    matches = matches.sort_values(by='satiety_score', ascending=False)
    
    print(f"\n--- Matching Foods for '{search_query}' (Sorted by Satiety) ---")
    with pd.option_context('display.max_rows', None, 'display.max_colwidth', None):
        print(matches[['Name']])
    
    choice = input("\nEnter the index number (ID) of the food you want: ")
    try:
        selected_food = int(choice)
        # Verify the choice was actually in our filtered list
        if selected_food in matches.index:
            print(f"Target locked: {foods.at[selected_food, 'Name']}\n")
        else:
            print("That ID was not in the filtered list. Running general optimization.\n")
            selected_food = None
    except (ValueError, KeyError):
        selected_food = None
        print("Invalid index. Running general optimization instead.\n")
else:
    selected_food = None
    print(f"No results found for '{search_query}' that aren't excluded.\n")


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


if selected_food is not None:
    # Add constraint to ensure the user-selected food is included in the meal plan
    prob += bin_vars[(selected_food)] == 1, f"Include_{selected_food}"

    prob += food_vars[(selected_food)] >= 1, f"Minimum_{selected_food}"



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