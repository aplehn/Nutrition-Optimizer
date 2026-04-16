import pandas as pd
import individualized_constraints as cons
import optimizer_modes as opmd
from pulp import HiGHS, LpProblem, LpMaximize, LpVariable, lpSum, LpStatus, LpInteger, LpContinuous, LpBinary
import re

mode = "Baseline"  # normal, rfk_jr, cookie_monster, bodybuilder, mediterranean, etc.
print(f"\nOptimization mode: {mode}")

nutrient_ranges = cons.get_nutrient_ranges(
# User inputs for personalized nutrition constraints
    sex = "male",
    age_years = 30,
    weight_kg = 68,
    height_cm = 165,
    activity_level = "moderate",
    goal = "maintain",  
    life_stage = "adult"
)

foods = pd.read_csv('FoodData_Categorized_v8.csv')
foods = foods.sample(frac=1).reset_index(drop=True) # shuffle the foods to encourage variety in the optimization results, we will also add some random jitter to the nutrient constraints to further encourage variety in meal plans
foods = foods.fillna(0)  # Fill missing nutrient values with 0

foods['Omega-3 Total (g)'] = (
    foods.get('Omega-3 EPA (g)', 0)
    + foods.get('Omega-3 DHA (g)', 0)
    + foods.get('Omega-3 ALA (g)', 0)
)

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
    'Omega_3': 'Omega-3 Total (g)',
    'Omega_6': 'Omega-6 (g)',
    
}



# Only keep nutrients that are in both cons.nutrient_ranges and name_map
valid_nutrients = [k for k in nutrient_ranges if k in name_map]

# Remove beverages (coffee, tea, soda, diet drinks, energy drinks, water) - these tend to have very low satiety scores and can skew the optimization
# Other removals: Nutritional supplements, # enriched foods
beverage_pattern = r'\b(?:coffee|tea|soda|diet|water|energy drink|soft drink|sugar substitute|nutritional|supplement|Baby|Toddler|vegetable protein|gelatin)\b' #"enriched"
foods = foods[~foods['Name'].str.contains(beverage_pattern, case=False, na=False)] 
foods = foods.reset_index(drop=True)

# Remove raw meats - these are typically not consumed in large quantities and can skew the optimization, also often have low satiety scores due to low protein digestibility when raw
meat_keywords = r'beef|chicken|pork|turkey|fish|salmon|tuna|lamb|veal|ham|bacon|sausage|duck|goat|shrimp|crab|lobster|clams|oysters|mussels|scallops|octopus|squid'
raw_meat_pattern = rf'(?i)(?=.*\braw\b)(?=.*\b(?:{meat_keywords})\b)'
foods = foods[~foods['Name'].str.contains(raw_meat_pattern, regex=True, na=False)]
foods = foods.reset_index(drop=True)

# Remove spices and other impractical edge cases
edge_pattern = r'\b(?:basil|oregano|thyme|rosemary|cilantro|parsley|dill|tarragon)\b'
foods = foods[~foods['Name'].str.contains(edge_pattern, case=False, na=False)] 
foods = foods.reset_index(drop=True)

# Define keywords for food groups we want to limit to 1 item per day (e.g., only one type of egg, one type of yogurt, etc.)
#keywords_to_limit = ['Egg', 'Yogurt', 'Milk', 'Cheese', 'Fish', 'Chicken', 'Beef', 'Pork', 'Tofu', 'Tempeh', 'Lentil', 'Bean', 'Nut', 'Seed']
keywords_to_limit = ['Egg', 'Yogurt', 'Milk','Tofu', 'Tempeh', 'Lentil', 'Fish', 'Chicken', 'Beef', 'Clams']
food_indices = foods.index.tolist()

# Intialize the Problem
prob = LpProblem("Meal_Plan_Optimization", LpMaximize)

# objective function
foods['e_density'] = foods['Calories (kcal)'] / foods['Portion size (g)'].replace(0, 100)
foods['satiety_score'] = (0.5 * foods['Protein (g)']) + (0.3 * foods['Fiber (g)']) - (0.2 * foods['e_density'])

#foods = opmd.apply_mode_scores(foods, mode, opmd.MODE_WEIGHTS)

foods = opmd.add_mode_features(foods)
foods = opmd.apply_mode_scores(foods, mode)


def exclusion_filter(name, query):
    safe_query = re.escape(query)
    # Excludes names containing "excluding [query]" while matching names containing the query
    pattern = rf"^(?!.*excluding.*{safe_query}).*{safe_query}"
    return bool(re.search(pattern, name, re.IGNORECASE))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt

console = Console()

# --- PHASE 1: GLOBAL EXCLUSIONS (BLACKLIST) ---
console.print(Panel("[bold red]PHASE 1: BLACKLIST (Remove Unwanted Foods)[/bold red]", expand=False))
excluded_indices = []

while True:
    exclude_query = Prompt.ask("\nSearch to [bold red]EXCLUDE[/bold red] (or [bold yellow]Enter[/bold yellow] to finish)")
    if not exclude_query: break

    # Direct ID Exclusion
    if exclude_query.isdigit():
        idx = int(exclude_query)
        if idx in foods.index:
            excluded_indices.append(idx)
            console.print(f"[bold red]Restricted:[/bold red] {foods.at[idx, 'Name']}")
        continue

    # Keyword Search for Exclusion
    matches = foods[foods['Name'].apply(lambda x: exclusion_filter(x, exclude_query))]
    if not matches.empty:
        matches = matches.sort_values(by='satiety_score', ascending=False)
        
        table = Table(title=f"Potential Exclusions for '{exclude_query}'", header_style="bold magenta")
        table.add_column("ID", justify="right", style="dim")
        table.add_column("Food Name")
        
        for idx, row in matches.head(None).iterrows():
            table.add_row(str(idx), row['Name'])
        console.print(table)
        
        action = Prompt.ask("Action", choices=["all", "id", "c"], default="all")
        if action == "all":
            excluded_indices.extend(matches.index.tolist())
            console.print(f"[bold red]Restricted all {len(matches)} items.[/bold red]")
        elif action == "id":
            target_id = IntPrompt.ask("Enter specific ID to exclude")
            if target_id in matches.index:
                excluded_indices.append(target_id)
                console.print(f"[bold red]Restricted:[/bold red] {foods.at[target_id, 'Name']}")
    else:
        console.print(f"[yellow]No results found for '{exclude_query}'.[/yellow]")

# Apply removals
if excluded_indices:
    foods = foods.drop(index=list(set(excluded_indices))).reset_index(drop=True)
    food_indices = foods.index.tolist()
    console.print(f"\n[bold green]Removing Complete.[/bold green] {len(foods)} food items remaining.")


# --- PHASE 2: MULTI-FOOD SEARCH AND SELECTION (INCLUDE) ---
console.print(Panel("[bold green]PHASE 2: SELECTION (Force Foods Into Plan)[/bold green]", expand=False))
selected_foods = []

while True:
    search_query = Prompt.ask("\nSearch to [bold green]INCLUDE[/bold green] (or [bold yellow]Enter[/bold yellow] to finish)")
    if not search_query: break

    matches = foods[foods['Name'].apply(lambda x: exclusion_filter(x, search_query))]

    if not matches.empty:
        matches = matches.sort_values(by='satiety_score', ascending=False)
        
        table = Table(title=f"Matches for '{search_query}'", header_style="bold cyan")
        table.add_column("ID", justify="right", style="dim")
        table.add_column("Food Name")
        table.add_column("Satiety")
        
        for idx, row in matches.head(None).iterrows():
            table.add_row(str(idx), row['Name'], f"{row['satiety_score']:.2f}")
        console.print(table)
        
        choice = Prompt.ask("Enter ID to add (or [bold yellow]c[/bold yellow] to cancel)")
        if choice.lower() == 'c': continue
        
        if choice.isdigit():
            food_idx = int(choice)
            if food_idx in foods.index:
                selected_foods.append(food_idx)
                console.print(f"[bold green]Added to Anchor List:[/bold green] {foods.at[food_idx, 'Name']}")
            else:
                console.print("[red]Invalid ID.[/red]")
    else:
        console.print(f"[yellow]No results for '{search_query}'.[/yellow]")
# After the user has finished entering foods, we print the final list of selected foods that will be forced into the meal plan optimization.
print(f"\nFinal list of forced foods: {[foods.at[i, 'Name'] for i in selected_foods]}")


# Create variables dynamically based on Optimization type column
food_vars = {}
bin_vars = {}
# We loop through each day and each food item, creating a variable for the amount of that food and a binary variable to indicate whether that food is included in the meal plan for that day.
for row in foods[['OptimizationType', 'FoodCategory']].itertuples(index=True):
    i = row.Index
    # use the index or a unique ID for the variable name
    var_name = f"food_{i}"
    bin_name = f"bin_{i}"

    # create binary switch
    bin_vars[(i)] = LpVariable(bin_name, cat=LpBinary)

    # if the optimization type is discrete, we want an integer variable (0, 1, 2, etc.) representing number of servings
    if row.OptimizationType == 'Discrete':
        # use integer variable for discrete optimization
        food_vars[(i)] = LpVariable(var_name, lowBound=0, upBound= 3, cat=LpInteger)

    else:
        # these can be continuous variables
        food_vars[(i)] = LpVariable(var_name, lowBound=0, upBound=3,cat=LpContinuous)

        # Determine the minimum allowed servings if the food is selected
    if row.FoodCategory in ['Fruit', 'Vegetable', 'Fruit & Vegetable']:
        min_servings = 2.0  # Force "a couple" of servings for produce
    elif row.FoodCategory == 'Meal':
        min_servings = 2.0  # For meals, at least 2 servings if selected
    else:
        min_servings = 0.1  # For other foods, at least 0.1 serving if selected
    
    # Add constraint to link binary variable with food variable
    prob += food_vars[(i)] <= 3 * bin_vars[(i)], f"Link_{i}_upper"
    prob += food_vars[(i)] >= min_servings * bin_vars[(i)], f"Link_{i}_lower"

    


# If the user has selected specific foods to include in their meal plan, we add constraints to the optimization problem to ensure those foods are included.
if selected_foods:
    for selected_food in selected_foods:
        # Add constraint to ensure the user-selected food is included in the meal plan
        name = foods.at[selected_food, 'Name']
        portion = foods.at[selected_food, 'Portion size (g)']
        minimum_amount = Prompt.ask(f"\nEnter minimum amount for {name} ({portion}g) (in servings, default 1)")
        if not minimum_amount:
            minimum_amount = 1
        else:
            minimum_amount = float(minimum_amount)
        prob += bin_vars[(selected_food)] == 1, f"Include_{selected_food}"
        prob += food_vars[(selected_food)] >= minimum_amount, f"Minimum_{selected_food}"



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
# prob += lpSum([food_vars[(i)] * foods.at[i, 'mode_score'] for i in food_indices])

slack_vars = {}
for nutrient in valid_nutrients:
    if nutrient in name_map:
        # Get the column name for this nutrient and the corresponding nutrient values for all foods
        col = name_map[nutrient]
        # Create a dictionary mapping food indices to their nutrient values for this nutrient
        food_data_dict = nutrient_values[col]
        # Create the sum of (food variable * nutrient value) for all foods
        nutrient_sum = lpSum([food_vars[(i)] * food_data_dict[i] for i in food_indices])
        
        # Get the lower and upper bounds for this nutrient from the constraints
        lower_bound, upper_bound = nutrient_ranges[nutrient]
        # Add some random jitter to the nutrient constraints to encourage variety in the meal plans

        low_slack = LpVariable(f"{nutrient}_low_slack", lowBound=0)
        up_slack = LpVariable(f"{nutrient}_up_slack", lowBound=0)
        slack_vars[nutrient] = {'low': low_slack, 'up': up_slack}

        if lower_bound is not None:
            prob += nutrient_sum + low_slack >= lower_bound, f"{nutrient}_min"

        if upper_bound is not None:
            prob += nutrient_sum - up_slack <= upper_bound, f"{nutrient}_max"

        #print(nutrient, lower_bound, upper_bound)

# update the objective function to penalize slacks
# we multiply the slacks by a very large number so the solver only uses them if it absolutely has to
penalty_weight = 1000000
prob += lpSum([food_vars[(i)] * foods.at[i, 'mode_score'] for i in food_indices]) - penalty_weight * lpSum([slack_vars[nutrient]['low'] + slack_vars[nutrient]['up'] for nutrient in valid_nutrients])


# identify indices for the categories meals
meal_indices = foods[foods['FoodCategory'] == 'Meal'].index.tolist()

prob += lpSum([bin_vars[i] for i in meal_indices]) >= 2, "At_Least_Two_Different_Meals"

# 1. Identify indices for the categories we created earlier
# We include 'Fruit & Vegetable' in both to be inclusive of mixed produce
fruit_indices = foods[foods['FoodCategory'].isin(['Fruit'])].index.tolist()
veg_indices = foods[foods['FoodCategory'].isin(['Vegetable', 'Fruit & Vegetable'])].index.tolist()

# 2. Define the total weight of all foods in the meal plan
# Weight = (number of servings) * (grams per serving)
total_weight = lpSum([food_vars[i] * foods.at[i, 'Portion size (g)'] for i in food_indices])

# 3. Define the weight for Fruits and Vegetables specifically
fruit_weight = lpSum([food_vars[i] * foods.at[i, 'Portion size (g)'] for i in fruit_indices])
veg_weight = lpSum([food_vars[i] * foods.at[i, 'Portion size (g)'] for i in veg_indices])

# 4. Add the Percentage Constraints
# Mathematical logic: Weight >= Total * 0.30
prob += fruit_weight >= 0.20 * total_weight, "Min_20_Percent_Fruit"
prob += veg_weight >= 0.30 * total_weight, "Min_30_Percent_Vegetables"
prob += lpSum([bin_vars[i] for i in fruit_indices]) >= 3, "At_Least_Three_Different_Fruits"
prob += lpSum([bin_vars[i] for i in veg_indices]) >= 3, "At_Least_Three_Different_Vegetables"


# solve problem
prob.solve(HiGHS(msg=False))

# 1. It starts as an empty dictionary
nutrient_totals = {}

# 2. It loops through every nutrient you defined as "valid"
for nutrient in valid_nutrients:
    col = name_map[nutrient]

    # 3. It performs a "Sum" calculation: 
    # (Servings chosen by solver) * (Nutrient amount in that food)
    total = sum(
        (food_vars[i].varValue or 0) * foods.at[i, col]
        for i in food_indices
    )

    # 4. It stores that result in the dictionary
    nutrient_totals[nutrient] = total

# Check for violations first
violations = []
for nutrient in valid_nutrients:
    val = nutrient_totals[nutrient]
    low, high = nutrient_ranges[nutrient]
    
    if low and val < (low - 0.01):
        violations.append(f"[SHORTFALL] {nutrient}: {val:.2f} (Minimum is {low})")
    if high and val > (high + 0.01):
        violations.append(f"[EXCESS] {nutrient}: {val:.2f} (Maximum is {high})")

if violations:
    print("THE FOLLOWING CONSTRAINTS WERE BROKEN:")
    for v in violations:
        print(f"  {v}")
else:
    print("All constraints successfully met.")

# output the meal plan
if LpStatus[prob.status] == 'Optimal':
    selected_foods = []

    # 1. Define the order of priority (Lower number = appears first)
    priority_map = {
        'Meal': 0,
        'Vegetable': 1,
        'Fruit': 2,
        'Fruit & Vegetable': 3,
        'Snack': 4,
        'Other': 5
    }

    # 2. Collect selected foods
    for i, category, name, portion_size in foods[['FoodCategory', 'Name', 'Portion size (g)']].itertuples(index=True, name=None):
        value = food_vars[i].varValue
        
        if value and value > 0:
            selected_foods.append({
                'category': category,
                'name': name,
                'portion_size': portion_size,
                'value': value,
                'is_integer': food_vars[i].cat == LpInteger
            })

    # 3. Sort using the priority map
    # .get(..., 99) is a safety net in case a category isn't in our map
    selected_foods.sort(key=lambda x: priority_map.get(x['category'], 99))

    # 4. Print the results
    print(f"--- Meal Plan ---")
    current_cat = None
    
    for item in selected_foods:
        # Optional: Print a header when the category changes
        if item['category'] != current_cat:
            current_cat = item['category']
            print(f"\n[{current_cat}s]") 
            
        if item['is_integer']:
            print(f" - {int(item['value'])} serving(s) of {item['name']}")
        else:
            amount = item['value'] * item['portion_size']
            print(f" - {amount:.2f} grams of {item['name']}")

else:
    print(f"No optimal solution found. Solver status: {LpStatus[prob.status]}")



# --- PRINT NUTRITIONAL PROFILE ---

print("\n--- Nutritional Profile of Meal Plan ---")

nutrient_totals = {}

for nutrient in valid_nutrients:
    col = name_map[nutrient]

    total = sum(
        (food_vars[i].varValue or 0) * foods.at[i, col]
        for i in food_indices
    )

    nutrient_totals[nutrient] = total

for nutrient in nutrient_totals:
    lower_bound, upper_bound = nutrient_ranges[nutrient]

    value = nutrient_totals[nutrient]

    if upper_bound is None:
        print(f"{nutrient:20} : {value:.2f} (min {lower_bound})")

    else:
        print(f"{nutrient:20} : {value:.2f} ({lower_bound} - {upper_bound})")


