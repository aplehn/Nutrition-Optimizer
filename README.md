# Nutrition-Optimizer
Problem Statement: 
Maintaining a calorie deficit is the most important factor in weight loss, however ensuring that a calorie 
deficit is maintained in a filling and nutritious way can be a challenge. Our project aims to create a meal 
plan optimizer that maximizes the satiety of a daily meal plan while considering all other dietary needs. A 
user will input desired eating choices into a calorie tracking app (ie. pizza at lunch, 1 candy bar) and 
export resulting nutrition data. Then, our optimizer will create the remainder of a diet plan that meets the 
rest of the user’s daily nutritional needs while staying under calorie constraints and optimizing for satiety. 
Variables: 
The optimizer will recommend an amount in grams for each of the 366 USDA foundation foods. This 
vector of recommended food quantities will be represented by “x” 
Objective Function:  
Our objective function will calculate a custom satiety score using protein, fiber, and calorie data. 
Minimize: -Σ (Satiety)i * xi 
Where: 
(Satiety)i = a * (protein)i + b * (fiber)i – c * (energy density)i 
(energy density)i = (kcalories)i/(gram)i 
The impact of varying weighting coefficients a, b, and c will be explored in our project. 
Constraints: 
It is recommended that a healthy diet should contain a wide variety of whole foods. However, a list of 
food recommendations that is too long can be impractical for the end user. To keep diet variety within a 
healthy, but reasonable range, our optimizer will contain upper and lower bounds on the quantity of 
nonzero x_i values in the result. 
Calorie limits will be set by the user in order to meet weight management goals. 
Other dietary considerations include minimum percent-by-mass values of fruit and vegetable entries. 
Each major macronutrient and micronutrient will be bounded by minimum and maximum values. These 
will include, but may not be limited to: carbs, fats (saturated, unsaturated, trans), protein, cholesterol, 
sodium, fiber, iron, calcium, vitamin A, vitamin C, Vitamins B12 & B6, Folate, Potassium, and Magnesium. 
Limitations: 
Our model will not consider subjective factors such as taste, preparation effort, recipe integration, and 
food norms. Available data also does not allow for monetary cost to be considered. Our optimizer will not 
consider variation in nutritional values due to methods of cooking. Complex interactions between 
nutrients and the differing nutritional needs for each individual will not be considered.