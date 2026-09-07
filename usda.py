import requests

from desserts_syn import SWEET_SYNONYMS


def search_with_synonyms(food_name, api_key):

    food_name = food_name.lower().strip()

    search_terms = SWEET_SYNONYMS.get(
        food_name,
        [food_name]
    )

    for term in search_terms:

        print("Searching USDA for:", term)

        params = {
            "api_key": api_key,
            "query": term,
            "pageSize": 5
        }

        response = requests.get(
            "https://api.nal.usda.gov/fdc/v1/foods/search",
            params=params
        )

        data = response.json()
        foods = data.get("foods", [])

        if foods:
            print("✅ Found using:", term)
            print("Matched:", foods[0]["description"])

            return foods

    print("❌ Not found in USDA:", food_name)

    return []

#===========================USDA returns the complete information about that food================================

def get_food_details(fdc_id, api_key):

    url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}"

    params = {
        "api_key": api_key
    }

    response = requests.get(url, params=params)

    response.raise_for_status()

    return response.json()

#==================================function to extract calories===========================
def get_calories(food_details):

    nutrients = food_details.get("foodNutrients", [])

    for item in nutrients:

        nutrient = item.get("nutrient", {})
        nutrient_name = nutrient.get("name", "")
        unit = nutrient.get("unitName", "")

        if nutrient_name == "Energy" and unit.upper() == "KCAL":
            return item.get("amount")

    return None 