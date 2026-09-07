

import streamlit as st
from google import genai
from PIL import Image
from dotenv import load_dotenv
import os
import json
import pandas as pd

from usda import search_with_synonyms, get_food_details


# =========================================================
# 1. Load API Keys
# =========================================================

load_dotenv()

USDA_API_KEY = os.getenv("USDA_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# =========================================================
# 2. Read Excel Dataset
# =========================================================

dessert_df = pd.read_excel("sugar_desserts.xlsx")


# =========================================================
# 3. Create Gemini Client
# =========================================================

client = genai.Client(api_key=GOOGLE_API_KEY)


# =========================================================
# 4. Search Sugar in Excel
# =========================================================

def get_sugar_from_excel(dessert_name):

    result = dessert_df[
        dessert_df["Dessert_name"].astype(str).str.lower().str.strip()
        == dessert_name.lower().strip()
    ]

    if not result.empty:
        return result.iloc[0]["Sugar_per_100g"]

    return None


# =========================================================
# 5. Gemini Sugar Agent - LAST OPTION
# =========================================================

def sugar_agent(dessert_name):

    agent_prompt = f"""
    You are a nutrition assistant.

    USDA and the local Excel dataset do not have
    a sugar value for:

    {dessert_name}

    Estimate the typical amount of sugar per 100 grams
    of this dessert.

    Return ONLY valid JSON in this format:

    {{
        "Sugar": 0,
        "Unit": "g",
        "Basis": "per 100g",
        "Confidence": 0,
        "Note": ""
    }}

    Rules:
    - Sugar must be a number.
    - Confidence must be between 0 and 100.
    - Clearly state in Note that this is an AI estimate.
    - Do not return markdown.
    - Return JSON only.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=agent_prompt
    )

    try:
        return json.loads(response.text)

    except json.JSONDecodeError:
        return None


# =========================================================
# 6. Extract Nutrition from USDA
# =========================================================

def get_nutrition(food_details):

    nutrients = {
        "Calories": None,
        "Protein": None,
        "Fat": None,
        "Carbohydrates": None,
        "Sugar": None,
        "Fiber": None
    }

    for nutrient in food_details["foodNutrients"]:

        name = nutrient["nutrient"]["name"]
        amount = nutrient.get("amount")

        if name == "Energy":
            nutrients["Calories"] = amount

        elif name == "Protein":
            nutrients["Protein"] = amount

        elif name == "Total lipid (fat)":
            nutrients["Fat"] = amount

        elif name == "Carbohydrate, by difference":
            nutrients["Carbohydrates"] = amount

        elif name == "Sugars, total including NLEA":
            nutrients["Sugar"] = amount

        elif name == "Fiber, total dietary":
            nutrients["Fiber"] = amount

    return nutrients


# =========================================================
# 7. Streamlit Page
# =========================================================

st.title("🍰 Arabic Dessert Calorie Tracker")

st.write("Upload an image of a dessert.")

uploaded_file = st.file_uploader(
    "Choose a dessert image",
    type=["jpg", "jpeg", "png"]
)


# =========================================================
# 8. IMAGE
# =========================================================

if uploaded_file is not None:

    image = Image.open(uploaded_file)

    st.image(
        image,
        caption="Uploaded Dessert"
    )


    # =====================================================
    # 9. GEMINI VISION
    # =====================================================

    prompt = """
    You are a food recognition expert.

    Look carefully at this dessert image.

    Identify the dessert.

    Estimate your confidence between 0 and 100.

    Return ONLY valid JSON.

    {
        "Dessert_Name": "",
        "Confidence": 0,
        "Description": ""
    }

    Rules:
    - Confidence must be an integer.
    - Confidence should represent your estimated certainty.
    - Do not return markdown.
    - Do not return explanations.
    - Return JSON only.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, image]
    )


    # =====================================================
    # 10. GET DESSERT NAME
    # =====================================================

    try:

        result = json.loads(response.text)

        dessert_name = result["Dessert_Name"]
        confidence = result["Confidence"]
        description = result["Description"]

        st.subheader("Gemini Result")

        st.write(
            "Dessert Name:",
            dessert_name
        )

        st.write(
            "Confidence:",
            confidence,
            "%"
        )

        st.write(
            "Description:",
            description
        )


        # =================================================
        # 11. SEARCH USDA
        # =================================================

        foods = search_with_synonyms(
            dessert_name,
            USDA_API_KEY
        )


        # =================================================
        # 12. DESSERT FOUND IN USDA?
        # =================================================

        if foods:

            # YES
            st.success(
                "Dessert found in USDA."
            )

            st.write(
                "USDA food match:",
                foods[0]["description"]
            )

            fdc_id = foods[0]["fdcId"]


            # =============================================
            # 13. GET NUTRITION FROM USDA
            # =============================================

            food_details = get_food_details(
                fdc_id,
                USDA_API_KEY
            )

            nutrition = get_nutrition(
                food_details
            )


            # =============================================
            # 14. DISPLAY NUTRITION
            # =============================================

            st.subheader(
                "Nutrition Information"
            )

            st.write(
                "Calories:",
                nutrition["Calories"]
            )

            st.write(
                "Protein:",
                nutrition["Protein"],
                "g"
            )

            st.write(
                "Fat:",
                nutrition["Fat"],
                "g"
            )

            st.write(
                "Carbohydrates:",
                nutrition["Carbohydrates"],
                "g"
            )

            st.write(
                "Fiber:",
                nutrition["Fiber"],
                "g"
            )


            # =============================================
            # 15. DOES USDA HAVE SUGAR?
            # =============================================

            if nutrition["Sugar"] is not None:

                # YES → USE USDA SUGAR

                st.success(
                    "Sugar found in USDA."
                )

                st.write(
                    "Sugar:",
                    nutrition["Sugar"],
                    "g"
                )

                st.caption(
                    "Source: USDA"
                )


            # =============================================
            # USDA DOES NOT HAVE SUGAR
            # =============================================

            else:

                st.warning(
                    "Sugar value is missing from USDA."
                )


                # =========================================
                # 16. SEARCH EXCEL
                # =========================================

                excel_sugar = get_sugar_from_excel(
                    dessert_name
                )


                # =========================================
                # 17. SUGAR FOUND IN EXCEL?
                # =========================================

                if excel_sugar is not None:

                    # YES → USE EXCEL SUGAR

                    st.success(
                        "Sugar found in Excel dataset."
                    )

                    st.write(
                        "Sugar:",
                        excel_sugar,
                        "g per 100g"
                    )

                    st.caption(
                        "Source: sugar_desserts.xlsx"
                    )


                # =========================================
                # SUGAR NOT FOUND IN EXCEL
                # =========================================

                else:

                    st.warning(
                        "Sugar not found in Excel."
                    )


                    # =====================================
                    # 18. GEMINI AGENT - LAST OPTION
                    # =====================================

                    sugar_result = sugar_agent(
                        dessert_name
                    )

                    if sugar_result:

                        st.subheader(
                            "🤖 Gemini Sugar Estimate"
                        )

                        st.write(
                            "Estimated Sugar:",
                            sugar_result["Sugar"],
                            "g per 100g"
                        )

                        st.write(
                            "AI Confidence:",
                            sugar_result["Confidence"],
                            "%"
                        )

                        st.caption(
                            sugar_result["Note"]
                        )

                    else:

                        st.error(
                            "Gemini could not estimate sugar."
                        )


        # =================================================
        # 19. DESSERT NOT FOUND IN USDA → ERROR
        # =================================================

        else:

            st.error(
                "Dessert not found in USDA."
            )


    # =====================================================
    # 20. GEMINI JSON ERROR
    # =====================================================

    except json.JSONDecodeError:

        st.error(
            "Gemini did not return valid JSON."
        )