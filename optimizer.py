# Import USDA Food Data
import json
with open('FoodData_Central_foundation_food_2025-12-18.json') as json_file:
    usda_food_data = json.load(json_file)