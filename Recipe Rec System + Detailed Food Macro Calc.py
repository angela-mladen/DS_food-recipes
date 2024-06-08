import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import tkinter as tk
from tkinter import messagebox, filedialog
import random

# Load the dataset
file_path = '/Users/angelamladenovska/Desktop/DS proj/final for proj/Reduced_Recipescl.csv'
recipes_df = pd.read_csv(file_path)

# Load the FoodMacro database
food_macro_file_path = '/Users/angelamladenovska/Desktop/DS proj/final for proj/FoodMacroDetailedInfo.csv'
food_macro_df = pd.read_csv(food_macro_file_path)

# Combine ingredients and instructions for each recipe
recipes_df['ingredients_combined'] = recipes_df.groupby('food_title')['ingredient'].transform(lambda x: '; '.join(x))
recipes_df['instructions_combined'] = recipes_df.groupby('food_title')['instructions'].transform(lambda x: x.iloc[0])
recipes_df = recipes_df[['food_title', 'ingredients_combined', 'instructions_combined']].drop_duplicates()

# Create the CountVectorizer and fit_transform on the dataset
vectorizer = CountVectorizer()
vectors = vectorizer.fit_transform(recipes_df['ingredients_combined'])

# Function to recommend recipes based on ingredients
def recommend_recipe(user_ingredients):
    user_ingredients_list = user_ingredients.split(", ")
    filtered_recipes = recipes_df[recipes_df['ingredients_combined'].apply(lambda x: all(ingredient in x for ingredient in user_ingredients_list))]
    
    if filtered_recipes.empty:
        return []
    
    filtered_vectors = vectorizer.transform(filtered_recipes['ingredients_combined'])
    user_vector = vectorizer.transform([user_ingredients])
    
    cosine_similarities = cosine_similarity(user_vector, filtered_vectors).flatten()
    
    # Get the indices of the top 5 most similar recipes
    top_indices = cosine_similarities.argsort()[-5:][::-1]
    
    recommended_recipes = filtered_recipes.iloc[top_indices]
    
    recommendations = []
    for index, row in recommended_recipes.iterrows():
        recommendations.append({
            'title': row['food_title'],
            'ingredients': row['ingredients_combined'],
            'instructions': row['instructions_combined']
        })
    
    return recommendations

# Function to display the chosen recipe in depth with bolded ingredients
def display_recipe(recipe, user_ingredients=None):
    recipe_window = tk.Toplevel(root)
    recipe_window.title(recipe['title'])
    recipe_window.configure(bg="#f0f8ff")
    recipe_window.geometry("600x700")  # Set a fixed size for the window

    title_label = tk.Label(recipe_window, text=recipe['title'], font=("Helvetica", 16, "bold"), bg="#f0f8ff")
    title_label.pack(pady=10)

    ingredients_text = tk.Text(recipe_window, wrap='word', font=("Helvetica", 12), bg="#f0f8ff", height=10, state='normal')
    ingredients_text.pack(padx=10, pady=10, fill='x', expand=False)
    ingredients_text.insert(tk.END, "Ingredients:\n")
    ingredients_text.tag_configure('bold', font=("Helvetica", 12, "bold"))

    ingredients = recipe['ingredients']
    if user_ingredients:
        for ingredient in user_ingredients.split(", "):
            start = 0
            while True:
                start = ingredients.lower().find(ingredient.lower(), start)
                if start == -1:
                    break
                end = start + len(ingredient)
                ingredients_text.insert(tk.END, ingredients[:start])
                ingredients_text.insert(tk.END, ingredients[start:end], 'bold')
                ingredients = ingredients[end:]
                start = 0
    ingredients_text.insert(tk.END, ingredients + "\n\n")
    ingredients_text.config(state='disabled')

    instructions_label = tk.Label(recipe_window, text="Instructions:", font=("Helvetica", 14, "bold"), bg="#f0f8ff")
    instructions_label.pack(pady=10)

    instructions_text = tk.Text(recipe_window, wrap='word', font=("Helvetica", 12), bg="#f0f8ff", state='normal')
    instructions_text.pack(padx=10, pady=10, fill='both', expand=True)
    instructions_text.insert(tk.END, recipe['instructions'])
    instructions_text.config(state='disabled')

    # Bind the Escape key to close the window
    recipe_window.bind('<Escape>', lambda e: recipe_window.destroy())

# Function to handle the button click event for recommending recipes
def on_recommend_button_click(event=None):
    user_ingredients = ingredients_entry.get()
    if user_ingredients:
        recommendations = recommend_recipe(user_ingredients)
        if recommendations:
            for widget in options_frame.winfo_children():
                widget.destroy()
            for i, recipe in enumerate(recommendations):
                button = tk.Button(options_frame, text=f"Option {i+1}: {recipe['title']}", command=lambda r=recipe: display_recipe(r, user_ingredients), font=("Helvetica", 12), bg="#d1e0e0", relief=tk.RAISED)
                button.pack(fill='x', padx=5, pady=5)
        else:
            messagebox.showinfo("No Recipe Found", "No recipe found with all the given ingredients.")
    else:
        messagebox.showwarning("Input Error", "Please enter some ingredients")

# Function to handle the Escape key event to close the application
def on_escape_key(event=None):
    for window in root.winfo_children():
        if isinstance(window, tk.Toplevel):
            window.destroy()
    root.quit()

# Function to display the FoodMacro database UI with scrolling, search, and toggleable fat content
def open_food_macro_ui():
    selected_items = []

    def update_results():
        result_text.config(state=tk.NORMAL)
        result_text.delete('1.0', tk.END)
        show_additional_fats = toggle_var.get()
        for index, row in food_macro_df.iterrows():
            details = f" {row['Food Name']} - Per 100 g: {row['Kcal']} kcal / {row['Protein']} g Protein / {row['Carbohydrate']} g Carbohydrates / {row['Fiber']} g Fiber / {row['Total Fat']} g Fat"
            if show_additional_fats:
                details += f" / {row['Saturated Fat']} g Saturated Fat / {row['Monounsaturated Fat']} g Monounsaturated Fat / {row['Polyunsaturated Fat']} g Polyunsaturated Fat / {row['Trans Fat']} g Trans Fat"
            add_button = tk.Button(result_text, text="Add", command=lambda food=row['Food Name']: add_food_to_list(food), font=("Helvetica", 10, "bold"), bg="#4CAF50", fg="black")
            result_text.window_create(tk.END, window=add_button)
            details += "\n" + "-" * 288 + "\n"
            result_text.insert(tk.END, f"{details}\n")
        result_text.config(state=tk.DISABLED)
    
    def find_next(event=None):
        query = search_entry.get()
        result_text.tag_remove('found', '1.0', tk.END)
        if query:
            start_pos = result_text.index(tk.INSERT)
            idx = result_text.search(query, start_pos, nocase=1, stopindex=tk.END)
            if not idx:
                idx = result_text.search(query, '1.0', nocase=1, stopindex=start_pos)
            if idx:
                end_pos = f"{idx}+{len(query)}c"
                result_text.tag_add('found', idx, end_pos)
                result_text.tag_config('found', background='yellow')
                result_text.mark_set(tk.INSERT, end_pos)
                result_text.see(idx)

    def add_food_to_list(food_name):
        amount = amount_entry.get()
        unit = unit_var.get()

        if amount and unit:
            try:
                amount = float(amount)
            except ValueError:
                messagebox.showerror("Input Error", "Please enter a valid number for the amount.")
                return

            selected_items.append((food_name, amount, unit))
            messagebox.showinfo("Item Added", f"Added {amount} {unit} of {food_name} to the list.")
        else:
            messagebox.showerror("Input Error", "Please enter the amount and select the unit.")

    def calculate_total_macros():
        total_kcal, total_protein, total_carbs, total_fat = 0, 0, 0, 0
        item_contributions = []

        for selected_food, amount, unit in selected_items:
            food_row = food_macro_df[food_macro_df['Food Name'] == selected_food].iloc[0]
            factor = 1
            if unit == 'grams':
                factor = amount / 100
            elif unit == 'cups':
                factor = amount * 240 / 100
            elif unit == 'tbsp':
                factor = amount * 15 / 100
            elif unit == 'tsp':
                factor = amount * 5 / 100
            elif unit == 'ounces':
                factor = amount * 28.35 / 100
            elif unit == 'pounds':
                factor = amount * 453.592 / 100

            kcal = food_row['Kcal'] * factor
            protein = food_row['Protein'] * factor
            carbs = food_row['Carbohydrate'] * factor
            fat = food_row['Total Fat'] * factor

            total_kcal += kcal
            total_protein += protein
            total_carbs += carbs
            total_fat += fat

            item_contributions.append(f"{selected_food} ({amount} {unit}): {kcal:.2f} kcal, {protein:.2f} g protein, {carbs:.2f} g carbs, {fat:.2f} g fat\n")

        macro_message = (
            f"Total Macros for Selected Items:\n"
            f"Calories: {total_kcal:.2f} kcal\n"
            f"Protein: {total_protein:.2f} g\n"
            f"Carbohydrates: {total_carbs:.2f} g\n"
            f"Fat: {total_fat:.2f} g\n\n"
            "Individual Contributions:\n" + "\n".join(item_contributions)
        )
        messagebox.showinfo("Total Macro Calculation", macro_message)

        # Ask the user if they want to save the output
        save_output = messagebox.askyesno("Save Output", "Do you want to save the calculated macros output?")
        if save_output:
            save_output_to_file(macro_message)

    def save_output_to_file(output):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            with open(file_path, 'w') as file:
                file.write(output)
            messagebox.showinfo("Output Saved", f"Output saved to {file_path}")

    def clear_selected_items():
        selected_items.clear()
        messagebox.showinfo("Clear List", "The list of selected items has been cleared.")

    # Create the new window
    food_macro_window = tk.Toplevel(root)
    food_macro_window.title("FoodMacro Database")
    food_macro_window.geometry("600x780")
    food_macro_window.configure(bg="#f0f8ff")
    
    # Create a frame to hold the search results
    results_frame = tk.Frame(food_macro_window, bg="#f0f8ff")
    results_frame.pack(fill='both', expand=True, pady=10)
    
    # Create a scrollbar
    scrollbar = tk.Scrollbar(results_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Create a text widget to display results
    result_text = tk.Text(results_frame, wrap='word', yscrollcommand=scrollbar.set, state=tk.NORMAL, font=("Helvetica", 10), bg="#f0f8ff")
    result_text.pack(fill='both', expand=True)
    scrollbar.config(command=result_text.yview)

    # Create a toggle button to show/hide additional fat contents
    toggle_var = tk.BooleanVar(value=True)
    toggle_button = tk.Checkbutton(food_macro_window, text="Show Additional Fat Contents", variable=toggle_var, command=update_results, font=("Helvetica", 12), bg="#f0f8ff")
    toggle_button.pack(pady=10)
    
    # Create a search entry and find next button
    search_entry = tk.Entry(food_macro_window, width=30, font=("Helvetica", 10))
    search_entry.pack(pady=5)
    find_button = tk.Button(food_macro_window, text="Find Next", command=find_next, font=("Helvetica", 10), bg="#4CAF50")
    find_button.pack(pady=5, padx=5)
    food_macro_window.bind('<Return>', find_next)

    # Create a frame for the calculation inputs
    calc_frame = tk.Frame(food_macro_window, bg="#f0f8ff")
    calc_frame.pack(pady=10)

    # Create an entry for the amount
    amount_label = tk.Label(calc_frame, text="Amount:", font=("Helvetica", 12), bg="#f0f8ff")
    amount_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')

    amount_entry = tk.Entry(calc_frame, width=10, font=("Helvetica", 10))
    amount_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')

    # Create a dropdown for units
    unit_var = tk.StringVar(value='grams')
    units = ['grams', 'cups', 'tbsp', 'tsp', 'ounces', 'pounds']
    unit_dropdown = tk.OptionMenu(calc_frame, unit_var, *units)
    unit_dropdown.config(font=("Helvetica", 10), bg="#f0f8ff")
    unit_dropdown.grid(row=0, column=2, padx=5, pady=5, sticky='w')

    # Create a calculate total macros button
    calculate_total_button = tk.Button(calc_frame, text="Calculate", command=calculate_total_macros, font=("Helvetica", 12), bg="#4CAF50")
    calculate_total_button.grid(row=1, column=1, pady=10, padx=5)

    # Create a clear list button
    clear_button = tk.Button(calc_frame, text="Clear List", command=clear_selected_items, font=("Helvetica", 12), bg="#f44336")
    clear_button.grid(row=1, column=2, pady=10, padx=5)

    # Bind the Escape key to close the window
    food_macro_window.bind('<Escape>', lambda e: food_macro_window.destroy())

    # Display the results initially
    update_results()

# Function to display a random recipe
def display_random_recipe():
    random_recipe = recipes_df.sample(n=1).iloc[0]
    recipe_details = {
        'title': random_recipe['food_title'],
        'ingredients': random_recipe['ingredients_combined'],
        'instructions': random_recipe['instructions_combined']
    }
    display_recipe(recipe_details)

# Create the main window
root = tk.Tk()
root.title("Recipe Recommendation System")

# Set the window size and make it not resizable
root.geometry("600x700")
root.resizable(False, False)

# Style settings
root.configure(bg="#f0f8ff")

# Bind the Enter key to the recommendation function
root.bind('<Return>', on_recommend_button_click)
# Bind the Escape key to close the application and all tabs
root.bind('<Escape>', on_escape_key)

# Create and place the input label
ingredients_label = tk.Label(root, text="Enter ingredients (comma separated):", font=("Helvetica", 14), bg="#f0f8ff")
ingredients_label.pack(pady=10)

# Create and place the input entry
ingredients_entry = tk.Entry(root, width=50, font=("Helvetica", 12))
ingredients_entry.pack(pady=5)

# Create and place the recommend button
recommend_button = tk.Button(root, text="Recommend Recipe", command=on_recommend_button_click, font=("Helvetica", 12), bg="#4CAF50",  relief=tk.RAISED)
recommend_button.pack(pady=10)

# Create and place the description label
description_label = tk.Label(root, text="Enter the ingredients you have, and we'll recommend recipes that match.\nClick on an option to see the recipe details.", font=("Helvetica", 12), bg="#f0f8ff", wraplength=450, justify="center")
description_label.pack(pady=10)

# Create a frame to hold the option buttons
options_frame = tk.Frame(root, bg="#f0f8ff")
options_frame.pack(fill='x', pady=10)

# Create and place the FoodMacro database button
food_macro_button = tk.Button(root, text="View FoodMacro Database", command=open_food_macro_ui, font=("Helvetica", 12), bg="#4CAF50", relief=tk.RAISED)
food_macro_button.pack(pady=10)

# Create and place the description label for FoodMacro
food_macro_description_label = tk.Label(root, text="Browse the FoodMacro database to find detailed nutritional information.\nClick 'Add' to add items to your list, then calculate the total macros.", font=("Helvetica", 12), bg="#f0f8ff", wraplength=450, justify="center")
food_macro_description_label.pack(pady=10)

# Create and place the surprise me button
surprise_me_button = tk.Button(root, text="Surprise Me with a Random Recipe", command=display_random_recipe, font=("Helvetica", 12), bg="#ff5733", relief=tk.RAISED)
surprise_me_button.pack(pady=10)

# Run the application
root.mainloop()
