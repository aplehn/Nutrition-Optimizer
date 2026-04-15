import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from optimizer_class import MealOptimizer, RunConfig
import individualized_constraints as cons


def build_result_row(result):
    row = {
        "mode": result.mode,
        "status": result.status,
        "objective_value": result.objective_value,
        "num_selected_foods": len(result.selected_foods),
    }
    row.update(result.nutrient_totals)
    return row


def plot_nutrient_totals(summary_df, nutrients_to_plot, title="Baseline vs Satiety: Nutrient Totals"):
    x = np.arange(len(nutrients_to_plot))
    width = 0.35

    baseline_vals = summary_df.loc[summary_df["mode"] == "Baseline", nutrients_to_plot].iloc[0].values
    satiety_vals = summary_df.loc[summary_df["mode"] == "normal", nutrients_to_plot].iloc[0].values

    plt.figure(figsize=(12, 6))
    plt.bar(x - width / 2, baseline_vals, width, label="Baseline")
    plt.bar(x + width / 2, satiety_vals, width, label="Satiety")

    plt.xticks(x, nutrients_to_plot, rotation=45, ha="right")
    plt.ylabel("Total Intake")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_percent_of_minimum(summary_df, nutrient_ranges, nutrients_to_plot, title="% of Minimum Requirement Met"):
    x = np.arange(len(nutrients_to_plot))
    width = 0.35

    baseline_pct = []
    satiety_pct = []

    for nutrient in nutrients_to_plot:
        lower_bound, _ = nutrient_ranges[nutrient]

        baseline_val = summary_df.loc[summary_df["mode"] == "Baseline", nutrient].iloc[0]
        satiety_val = summary_df.loc[summary_df["mode"] == "normal", nutrient].iloc[0]

        if lower_bound is None or lower_bound == 0:
            baseline_pct.append(np.nan)
            satiety_pct.append(np.nan)
        else:
            baseline_pct.append(100 * baseline_val / lower_bound)
            satiety_pct.append(100 * satiety_val / lower_bound)

    plt.figure(figsize=(12, 6))
    plt.bar(x - width / 2, baseline_pct, width, label="Baseline")
    plt.bar(x + width / 2, satiety_pct, width, label="Satiety")
    plt.axhline(100, linestyle="--", linewidth=1, label="Minimum requirement")

    plt.xticks(x, nutrients_to_plot, rotation=45, ha="right")
    plt.ylabel("% of Minimum Requirement")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_food_category_comparison(results, title="Baseline vs Satiety: Food Category Composition"):
    # Collect grams by category for each result
    rows = []
    for result in results:
        category_totals = {}
        for item in result.selected_foods:
            category = item["category"]
            grams = item["grams"]
            category_totals[category] = category_totals.get(category, 0) + grams

        row = {"mode": result.mode}
        row.update(category_totals)
        rows.append(row)

    df = pd.DataFrame(rows).fillna(0).set_index("mode")

    # Convert to percentages of total grams
    df_pct = df.div(df.sum(axis=1), axis=0) * 100

    df_pct.T.plot(kind="bar", figsize=(12, 6))
    plt.ylabel("% of Total Food Mass")
    plt.title(title)
    plt.xticks(rotation=45, ha="right")
    plt.legend(title="Mode")
    plt.tight_layout()
    plt.show()


def print_selected_foods(result):
    print(f"\n--- {result.mode} selected foods ---")
    for item in result.selected_foods:
        if item["is_integer"]:
            print(f"{item['servings']:.0f} serving(s) of {item['name']}")
        else:
            print(f"{item['grams']:.2f} g of {item['name']}")


def main():
    # ---------------------------------------
    # 1. Create optimizer
    # ---------------------------------------
    optimizer = MealOptimizer("FoodData_Categorized_v8.csv")

    # ---------------------------------------
    # 2. Common profile for both runs
    # ---------------------------------------
    common_kwargs = dict(
        sex="male",
        age_years=30,
        weight_kg=68,
        height_cm=165,
        activity_level="moderate",
        goal="maintain",
        life_stage="adult",
        forced_food_names=[],
        excluded_food_names=[],
        require_two_meals=True,
        min_fruit_fraction=0.20,
        min_veg_fraction=0.30,
        min_distinct_fruits=3,
        min_distinct_vegetables=3,
        use_slacks=True,
        slack_penalty=1_000_000,
        shuffle_foods=False,   # keep false for fair comparison
        random_seed=42,
    )

    # ---------------------------------------
    # 3. Build configs
    # ---------------------------------------
    baseline_config = RunConfig(
        mode="Baseline",
        **common_kwargs
    )

    satiety_config = RunConfig(
        mode="normal",
        **common_kwargs
    )

    # ---------------------------------------
    # 4. Run optimizer twice
    # ---------------------------------------
    baseline_result = optimizer.solve(baseline_config)
    satiety_result = optimizer.solve(satiety_config)

    results = [baseline_result, satiety_result]

    # ---------------------------------------
    # 5. Print quick summaries
    # ---------------------------------------
    for result in results:
        print(f"\nMode: {result.mode}")
        print(f"Status: {result.status}")
        print(f"Objective value: {result.objective_value}")
        print(f"Violations: {result.violations}")
        print_selected_foods(result)

    # ---------------------------------------
    # 6. Create summary DataFrame
    # ---------------------------------------
    summary_rows = [build_result_row(r) for r in results]
    summary_df = pd.DataFrame(summary_rows)

    print("\n--- Summary table ---")
    print(summary_df.T)

    # ---------------------------------------
    # 7. Recreate nutrient ranges for plotting
    # ---------------------------------------
    nutrient_ranges = cons.get_nutrient_ranges(
        sex=common_kwargs["sex"],
        age_years=common_kwargs["age_years"],
        weight_kg=common_kwargs["weight_kg"],
        height_cm=common_kwargs["height_cm"],
        activity_level=common_kwargs["activity_level"],
        goal=common_kwargs["goal"],
        life_stage=common_kwargs["life_stage"],
    )

    # ---------------------------------------
    # 8. Figures
    # ---------------------------------------
    nutrients_to_plot_totals = [
        "Energy", "Protein", "Fiber", "Fat", "Iron", "Calcium", "Vitamin_C", "Sodium"
    ]

    plot_nutrient_totals(
        summary_df,
        nutrients_to_plot_totals,
        title="Baseline vs Satiety: Nutrient Totals"
    )

    nutrients_to_plot_pct = [
        "Protein", "Fiber", "Iron", "Calcium", "Vitamin_C", "Vitamin_D", "Omega_3"
    ]

    plot_percent_of_minimum(
        summary_df,
        nutrient_ranges,
        nutrients_to_plot_pct,
        title="Baseline vs Satiety: % of Minimum Requirement Met"
    )

    plot_food_category_comparison(
        results,
        title="Baseline vs Satiety: Food Category Composition"
    )


if __name__ == "__main__":
    main()