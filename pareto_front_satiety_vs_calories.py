import pandas as pd
import matplotlib.pyplot as plt

from optimizer_class import MealOptimizer, RunConfig


def make_pareto_front():
    optimizer = MealOptimizer("FoodData_Categorized_v8.csv")

    # Common profile for all runs
    common_kwargs = dict(
        mode="normal",
        sex="male",
        age_years=30,
        weight_kg=68,
        height_cm=165,
        activity_level="moderate",
        goal="maintain",
        life_stage="adult",
        forced_food_names=[],
        excluded_food_names=[],
        forced_food_min_servings={},
        require_two_meals=True,
        min_fruit_fraction=0.20,
        min_veg_fraction=0.30,
        min_distinct_fruits=3,
        min_distinct_vegetables=3,
        use_slacks=False,          # strongly recommended for a Pareto front
        shuffle_foods=False,       # keep deterministic
        random_seed=42,
        override_energy_bounds=True,
        custom_objective_mode="normal",
    )

    # Calorie caps to sweep
    calorie_caps = list(range(1800, 3401, 100))

    results = []

    for cap in calorie_caps:
        cfg = RunConfig(
            calorie_cap=cap,
            **common_kwargs
        )

        result = optimizer.solve(cfg)

        if result.status == "Optimal":
            total_calories = result.nutrient_totals["Energy"]

            # Recompute total satiety from selected foods
            # Since the result stores selected foods, we only need the summed objective proxy.
            # If you want exact satiety, it's better to expose it directly from the class later.
            total_satiety_proxy = 0.0
            for item in result.selected_foods:
                # This is only a placeholder if mode_score is not returned explicitly.
                # If possible, expose mode_score totals directly in the class.
                pass

            # For now, use objective value when slacks are off.
            total_satiety = result.objective_value

            results.append({
                "calorie_cap": cap,
                "total_calories": total_calories,
                "total_satiety": total_satiety,
                "status": result.status,
                "num_foods": len(result.selected_foods),
            })
        else:
            print(f"Cap {cap}: {result.status}")

    pareto_df = pd.DataFrame(results)
    print(pareto_df)

    # Save results
    pareto_df.to_csv("pareto_satiety_vs_calories.csv", index=False)

    # Plot
    plt.figure(figsize=(8, 6))
    plt.plot(
        pareto_df["total_calories"],
        pareto_df["total_satiety"],
        marker="o"
    )
    plt.xlabel("Total Calories (kcal)")
    plt.ylabel("Total Satiety Objective")
    plt.title("Pareto Front: Satiety vs Calories")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    return pareto_df


if __name__ == "__main__":
    make_pareto_front()