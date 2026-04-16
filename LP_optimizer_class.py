from jax import config
import pandas as pd
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional

import individualized_constraints as cons
import optimizer_modes as opmd
from pulp import (
    HiGHS, LpProblem, LpMaximize, LpVariable, lpSum,
    LpStatus, LpInteger, LpContinuous, LpBinary, value
)


@dataclass
class RunConfig:
    mode: str = "normal"
    sex: str = "male"
    age_years: int = 30
    weight_kg: float = 68
    height_cm: float = 165
    activity_level: str = "moderate"
    goal: str = "maintain"
    life_stage: str = "adult"

    forced_food_names: List[str] = field(default_factory=list)
    excluded_food_names: List[str] = field(default_factory=list)
    forced_food_min_servings: Dict[str, float] = field(default_factory=dict)

    calorie_cap: Optional[float] = None
    override_energy_bounds: bool = False
    custom_objective_mode: Optional[str] = None   # optional, lets you force "normal" for Pareto runs

    require_two_meals: bool = True
    min_fruit_fraction: float = 0.20
    min_veg_fraction: float = 0.30
    min_distinct_fruits: int = 3
    min_distinct_vegetables: int = 3

    use_slacks: bool = True
    slack_penalty: float = 1_000_000
    shuffle_foods: bool = True
    random_seed: Optional[int] = None


@dataclass
class OptimizationResult:
    status: str
    mode: str
    objective_value: Optional[float]
    selected_foods: List[dict]
    nutrient_totals: Dict[str, float]
    violations: List[str]


class MealOptimizer:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path

        self.name_map = {
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

        self.base_foods = self._load_base_foods()

    def _load_base_foods(self) -> pd.DataFrame:
        foods = pd.read_csv(self.csv_path)
        foods = foods.fillna(0)

        foods['Omega-3 Total (g)'] = (
            foods.get('Omega-3 EPA (g)', 0)
            + foods.get('Omega-3 DHA (g)', 0)
            + foods.get('Omega-3 ALA (g)', 0)
        )

        return foods

    def _preprocess_foods(self, config: RunConfig) -> pd.DataFrame:
        foods = self.base_foods.copy()

        if config.shuffle_foods:
            foods = foods.sample(frac=1, random_state=config.random_seed).reset_index(drop=True)
        else:
            foods = foods.reset_index(drop=True)

        beverage_pattern = r'\b(?:coffee|tea|soda|diet|water|energy drink|soft drink|sugar substitute|nutritional|supplement|Baby|Toddler|vegetable protein|gelatin)\b'
        foods = foods[~foods['Name'].str.contains(beverage_pattern, case=False, na=False)]

        meat_keywords = r'beef|chicken|pork|turkey|fish|salmon|tuna|lamb|veal|ham|bacon|sausage|duck|goat|shrimp|crab|lobster|clams|oysters|mussels|scallops|octopus|squid'
        raw_meat_pattern = rf'(?i)(?=.*\braw\b)(?=.*\b(?:{meat_keywords})\b)'
        foods = foods[~foods['Name'].str.contains(raw_meat_pattern, regex=True, na=False)]

        edge_pattern = r'\b(?:basil|oregano|thyme|rosemary|cilantro|parsley|dill|tarragon)\b'
        foods = foods[~foods['Name'].str.contains(edge_pattern, case=False, na=False)]

        for name in config.excluded_food_names:
            foods = foods[~foods['Name'].str.contains(re.escape(name), case=False, na=False)]

        foods = foods.reset_index(drop=True)

        foods['e_density'] = foods['Calories (kcal)'] / foods['Portion size (g)'].replace(0, 100)
        foods['satiety_score'] = (
            0.5 * foods['Protein (g)']
            + 0.3 * foods['Fiber (g)']
            - 0.2 * foods['e_density']
        )

        foods = opmd.add_mode_features(foods)
        objective_mode = config.custom_objective_mode or config.mode
        foods = opmd.apply_mode_scores(foods, objective_mode)

        return foods

    def _match_food_indices(self, foods: pd.DataFrame, names: List[str]) -> List[int]:
        indices = []
        for target in names:
            exact = foods.index[foods['Name'].str.fullmatch(target, case=False, na=False)].tolist()
            if exact:
                indices.append(exact[0])
                continue

            partial = foods.index[foods['Name'].str.contains(re.escape(target), case=False, na=False)].tolist()
            if partial:
                indices.append(partial[0])
        return indices

    def solve(self, config: RunConfig) -> OptimizationResult:
        foods = self._preprocess_foods(config)
        nutrient_ranges = cons.get_nutrient_ranges(
            sex=config.sex,
            age_years=config.age_years,
            weight_kg=config.weight_kg,
            height_cm=config.height_cm,
            activity_level=config.activity_level,
            goal=config.goal,
            life_stage=config.life_stage,
        )

        valid_nutrients = [k for k in nutrient_ranges if k in self.name_map]
        food_indices = foods.index.tolist()

        forced_indices = self._match_food_indices(foods, config.forced_food_names)

        keywords_to_limit = ['Egg', 'Yogurt', 'Milk', 'Tofu', 'Tempeh', 'Lentil', 'Fish', 'Chicken', 'Beef', 'Clams']

        prob = LpProblem("Meal_Plan_Optimization", LpMaximize)

        food_vars = {}
        bin_vars = {}

        for row in foods[['OptimizationType', 'FoodCategory']].itertuples(index=True):
            i = row.Index

            bin_vars[i] = LpVariable(f"bin_{i}", cat=LpBinary)

            if row.OptimizationType == 'Discrete':
                food_vars[i] = LpVariable(f"food_{i}", lowBound=0, upBound=3, cat=LpInteger)
            else:
                food_vars[i] = LpVariable(f"food_{i}", lowBound=0, upBound=3, cat=LpContinuous)

            if row.FoodCategory in ['Fruit', 'Vegetable', 'Fruit & Vegetable']:
                min_servings = 2.0
            elif row.FoodCategory == 'Meal':
                min_servings = 2.0
            else:
                min_servings = 0.1

            prob += food_vars[i] <= 3 * bin_vars[i], f"Link_{i}_upper"
            prob += food_vars[i] >= min_servings * bin_vars[i], f"Link_{i}_lower"

        for i in forced_indices:
            name = foods.at[i, 'Name']
            minimum_amount = config.forced_food_min_servings.get(name, 1.0)
            prob += bin_vars[i] == 1, f"Include_{i}"
            prob += food_vars[i] >= minimum_amount, f"Minimum_{i}"

        keyword_groups = {}
        food_names = foods['Name'].astype(str)
        for word in keywords_to_limit:
            matching_indices = food_names[food_names.str.contains(word, case=False, na=False)].index.tolist()
            if matching_indices:
                keyword_groups[word] = matching_indices

        for word, group_indices in keyword_groups.items():
            prob += lpSum(bin_vars[i] for i in group_indices) <= 1, f"Limit_{word}"

        slack_vars = {}
        #############
        for nutrient in valid_nutrients:
            col = self.name_map[nutrient]
            nutrient_sum = lpSum(food_vars[i] * foods.at[i, col] for i in food_indices)
            lower_bound, upper_bound = nutrient_ranges[nutrient]

            # During Pareto runs, skip the normal Energy bounds and use calorie_cap instead
            if config.override_energy_bounds and nutrient == "Energy":
                continue

            if config.use_slacks:
                low_slack = LpVariable(f"{nutrient}_low_slack", lowBound=0)
                up_slack = LpVariable(f"{nutrient}_up_slack", lowBound=0)
                slack_vars[nutrient] = {'low': low_slack, 'up': up_slack}

                if lower_bound is not None:
                    prob += nutrient_sum + low_slack >= lower_bound, f"{nutrient}_min"

                if upper_bound is not None:
                    prob += nutrient_sum - up_slack <= upper_bound, f"{nutrient}_max"
            else:
                if lower_bound is not None:
                    prob += nutrient_sum >= lower_bound, f"{nutrient}_min"

                if upper_bound is not None:
                    prob += nutrient_sum <= upper_bound, f"{nutrient}_max"
        if config.calorie_cap is not None:
            calorie_sum = lpSum(food_vars[i] * foods.at[i, 'Calories (kcal)'] for i in food_indices)
            prob += calorie_sum <= config.calorie_cap, "Pareto_Calorie_Cap"
        if config.require_two_meals:
            meal_indices = foods[foods['FoodCategory'] == 'Meal'].index.tolist()
            prob += lpSum(bin_vars[i] for i in meal_indices) >= 2, "At_Least_Two_Different_Meals"

        fruit_indices = foods[foods['FoodCategory'].isin(['Fruit'])].index.tolist()
        veg_indices = foods[foods['FoodCategory'].isin(['Vegetable', 'Fruit & Vegetable'])].index.tolist()

        total_weight = lpSum(food_vars[i] * foods.at[i, 'Portion size (g)'] for i in food_indices)
        fruit_weight = lpSum(food_vars[i] * foods.at[i, 'Portion size (g)'] for i in fruit_indices)
        veg_weight = lpSum(food_vars[i] * foods.at[i, 'Portion size (g)'] for i in veg_indices)

        prob += fruit_weight >= config.min_fruit_fraction * total_weight, "Min_Fruit_Fraction"
        prob += veg_weight >= config.min_veg_fraction * total_weight, "Min_Veg_Fraction"
        prob += lpSum(bin_vars[i] for i in fruit_indices) >= config.min_distinct_fruits, "Min_Distinct_Fruits"
        prob += lpSum(bin_vars[i] for i in veg_indices) >= config.min_distinct_vegetables, "Min_Distinct_Vegetables"

        food_objective = lpSum(food_vars[i] * foods.at[i, 'mode_score'] for i in food_indices)

        if config.use_slacks:
            slack_penalty = config.slack_penalty * lpSum(
                slack_vars[n]['low'] + slack_vars[n]['up'] for n in valid_nutrients
            )
            prob += food_objective - slack_penalty
        else:
            prob += food_objective

        prob.solve(HiGHS(msg=False))

        status = LpStatus[prob.status]
        objective_value = value(prob.objective) if status in ("Optimal", "Feasible") else None

        nutrient_totals = {}
        for nutrient in valid_nutrients:
            col = self.name_map[nutrient]
            nutrient_totals[nutrient] = sum(
                (food_vars[i].varValue or 0) * foods.at[i, col] for i in food_indices
            )

        violations = []
        for nutrient in valid_nutrients:
            val = nutrient_totals[nutrient]
            low, high = nutrient_ranges[nutrient]

            if low is not None and val < low - 0.01:
                violations.append(f"[SHORTFALL] {nutrient}: {val:.2f} (Minimum is {low})")
            if high is not None and val > high + 0.01:
                violations.append(f"[EXCESS] {nutrient}: {val:.2f} (Maximum is {high})")

        selected_foods = []
        for i, category, name, portion_size in foods[['FoodCategory', 'Name', 'Portion size (g)']].itertuples(index=True, name=None):
            v = food_vars[i].varValue
            if v is None or v <= 0:
                continue

            selected_foods.append({
                "category": category,
                "name": name,
                "servings": float(v),
                "grams": float(v * portion_size),
                "is_integer": foods.at[i, 'OptimizationType'] == 'Discrete',
            })

        return OptimizationResult(
            status=status,
            mode=config.mode,
            objective_value=objective_value,
            selected_foods=selected_foods,
            nutrient_totals=nutrient_totals,
            violations=violations,
        )