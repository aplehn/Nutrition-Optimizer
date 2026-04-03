import cvxpy as cp
import pandas as pd
import numpy as np
import time
import constraints as cons

# 1. Load Data
foods = pd.read_csv('FoodData_Sorted_Filtered.csv').fillna(0)
foods = foods[~foods['Name'].str.contains('coffee|tea|soda|diet|energy drink|water|soft drink|sugar substitute', case=False, na=False)] 

def optimize_diet(df, nutrient_ranges, name_map):
    n = len(df)
    
    # --- Define Decision Variable ---
    x = cp.Variable(n, nonneg=True)
    
    
    # --- Build Satiety Objective ---
    e_density = df['Calories (kcal)'] / df['Portion size (g)'].replace(0, 100)
    satiety_per_unit = (0.5 * df['Protein (g)']) + (0.3 * df['Fiber (g)']) - (0.2 * e_density)
    coeffs = -satiety_per_unit.values
    objective = cp.Minimize(cp.sum(cp.multiply(coeffs, x)))
    
    # --- Build Constraints ---
    # Start with basic portion limits
    constraints = [x <= 10] 
    
    for nutrient, (min_val, max_val) in nutrient_ranges.items():
        col = name_map.get(nutrient, nutrient)
        
        if col in df.columns:
            # Vectorized multiplication of portions * nutrient density
            total_intake = cp.sum(cp.multiply(df[col].values, x))
            constraints.append(total_intake >= min_val)
            constraints.append(total_intake <= max_val)
        else:
            print(f"Warning: {nutrient} ({col}) not found in data.")

    # --- Solve ---
    prob = cp.Problem(objective, constraints)
    # Using CLARABEL solver (often better for large nutrient problems)
    prob.solve(solver=cp.CLARABEL) 
    
    if prob.status not in ["optimal", "feasible"]:
        print(f"Solver Status: {prob.status}. The constraints might be too strict!")
        return None, None

    df['Optimal_Portions'] = x.value
    return df, prob.value



# Execute
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
    'Omega_6': 'Omega-6 (g)'
}




start_time = time.perf_counter()
final_results, score = optimize_diet(foods, cons.nutrient_ranges, name_map)
elapsed_time = time.perf_counter() - start_time


for item in final_results:
    if final_results['Optimal_Portions'] is not int():
        print(f"{item}: {final_results[item].values}")

if final_results is not None:
    print(f"Optimization completed in {elapsed_time:.4f} seconds")
    print(f"Optimal Negative Satiety: {score}")
    print(final_results[final_results['Optimal_Portions'] > 1e-4][['Name', 'Optimal_Portions']])