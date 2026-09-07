
import streamlit as st
from google import genai
from PIL import Image
from dotenv import load_dotenv
import os
import json

from usda import search_with_synonyms, get_food_details
from rag import search_rag


# =========================================================
# 1. LOAD API KEYS
# =========================================================

load_dotenv()

USDA_API_KEY = os.getenv("USDA_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# =========================================================
# 2. CREATE GEMINI CLIENT
# =========================================================

client = genai.Client(
    api_key=GOOGLE_API_KEY
)


# =========================================================
# 3. GEMINI SUGAR AGENT - LAST OPTION
# =========================================================

def sugar_agent(dessert_name):

    agent_prompt = f"""
    You are a nutrition assistant.

    USDA and the local RAG dataset could not provide
    a reliable sugar value for:

    {dessert_name}

    Estimate the typical amount of sugar per 100 grams
    of this dessert.

    Return ONLY valid JSON:

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
# 4. RAG + GEMINI AGENT
# =========================================================

def rag_sugar_agent(dessert_name, rag_results):

    context = "\n".join(rag_results)

    rag_prompt = f"""
    You are a nutrition assistant.

    The following information was retrieved from
    a local dessert dataset using embeddings and FAISS.

    RETRIEVED CONTEXT:

    {context}

    DESSERT IDENTIFIED FROM IMAGE:

    {dessert_name}

    Find the best matching dessert in the retrieved
    information.

    Use ONLY the retrieved information.

    Do NOT estimate a sugar value.
    Do NOT use outside knowledge.

    Return ONLY valid JSON:

    {{
        "Dessert_Name": "",
        "Sugar": 0,
        "Unit": "g",
        "Basis": "per 100g"
    }}

    Do not return markdown.
    Return JSON only.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=rag_prompt
    )

    try:
        return json.loads(response.text)

    except json.JSONDecodeError:
        return None


# =========================================================
# 5. EXTRACT NUTRITION FROM USDA
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

    for nutrient in food_details.get(
        "foodNutrients",
        []
    ):

        nutrient_info = nutrient.get(
            "nutrient",
            {}
        )

        name = nutrient_info.get("name")

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
# 6. FUNCTION TO USE RAG
# =========================================================

def use_rag(dessert_name):

    st.info(
        "Searching local RAG database..."
    )

    # -----------------------------------------------------
    # Convert question to embedding and search FAISS
    # -----------------------------------------------------

    rag_results = search_rag(
        dessert_name,
        k=3
    )

    if not rag_results:

        return None

    # -----------------------------------------------------
    # OPTIONAL: Show retrieved information
    # -----------------------------------------------------

    with st.expander(
        "View RAG retrieved documents"
    ):

        for number, document in enumerate(
            rag_results,
            start=1
        ):

            st.write(
                f"Result {number}:"
            )

            st.write(document)

    # -----------------------------------------------------
    # Send retrieved information to Gemini
    # -----------------------------------------------------

    rag_result = rag_sugar_agent(
        dessert_name,
        rag_results
    )

    return rag_result


# =========================================================
# 7. STREAMLIT PAGE
# =========================================================

st.title(
    "🍰 Arabic Dessert Calorie Tracker"
)

st.write(
    "Upload an image of a dessert."
)

uploaded_file = st.file_uploader(
    "Choose a dessert image",
    type=[
        "jpg",
        "jpeg",
        "png"
    ]
)


# =========================================================
# 8. IMAGE UPLOADED
# =========================================================

if uploaded_file is not None:

    image = Image.open(
        uploaded_file
    )

    st.image(
        image,
        caption="Uploaded Dessert"
    )


    # =====================================================
    # 9. GEMINI VISION
    # =====================================================

    vision_prompt = """
    You are a food recognition expert.

    Look carefully at this dessert image.

    Identify the dessert.

    Estimate your confidence between 0 and 100.

    Return ONLY valid JSON:

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

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                vision_prompt,
                image
            ]
        )


        # =================================================
        # 10. READ GEMINI RESULT
        # =================================================

        result = json.loads(
            response.text
        )

        dessert_name = result[
            "Dessert_Name"
        ]

        confidence = result[
            "Confidence"
        ]

        description = result[
            "Description"
        ]


        # =================================================
        # 11. DISPLAY GEMINI RESULT
        # =================================================

        st.subheader(
            "Gemini Vision Result"
        )

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
        # 12. SEARCH USDA
        # =================================================

        st.info(
            "Searching USDA..."
        )

        foods = search_with_synonyms(
            dessert_name,
            USDA_API_KEY
        )


        # =================================================
        # 13. DESSERT FOUND IN USDA
        # =================================================

        if foods:

            st.success(
                "Dessert found in USDA."
            )

            st.write(
                "USDA food match:",
                foods[0]["description"]
            )

            fdc_id = foods[0]["fdcId"]


            # =============================================
            # 14. GET USDA DETAILS
            # =============================================

            food_details = get_food_details(
                fdc_id,
                USDA_API_KEY
            )

            nutrition = get_nutrition(
                food_details
            )


            # =============================================
            # 15. DISPLAY USDA NUTRITION
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
            # 16. USDA HAS SUGAR
            # =============================================

            if nutrition["Sugar"] is not None:

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
            # 17. USDA DOES NOT HAVE SUGAR → RAG
            # =============================================

            else:

                st.warning(
                    "Sugar value is missing from USDA."
                )

                rag_result = use_rag(
                    dessert_name
                )


                # =========================================
                # 18. RAG SUCCESS
                # =========================================

                if rag_result:

                    st.success(
                        "Sugar found using RAG."
                    )

                    st.write(
                        "Matched Dessert:",
                        rag_result[
                            "Dessert_Name"
                        ]
                    )

                    st.write(
                        "Sugar:",
                        rag_result["Sugar"],
                        "g per 100g"
                    )

                    st.caption(
                        "Source: Local dataset + "
                        "Embeddings + FAISS RAG"
                    )


                # =========================================
                # 19. RAG FAILED → GEMINI ESTIMATE
                # =========================================

                else:

                    st.warning(
                        "RAG could not find sugar information."
                    )

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
                            sugar_result[
                                "Confidence"
                            ],
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
        # 20. DESSERT NOT FOUND IN USDA → TRY RAG
        # =================================================

        else:

            st.warning(
                "Dessert not found in USDA."
            )

            st.info(
                "Trying local RAG database..."
            )

            rag_result = use_rag(
                dessert_name
            )


            # =============================================
            # 21. RAG SUCCESS
            # =============================================

            if rag_result:

                st.success(
                    "Dessert information found using RAG."
                )

                st.write(
                    "Matched Dessert:",
                    rag_result[
                        "Dessert_Name"
                    ]
                )

                st.write(
                    "Sugar:",
                    rag_result["Sugar"],
                    "g per 100g"
                )

                st.caption(
                    "Source: Local dataset + "
                    "Embeddings + FAISS RAG"
                )


            # =============================================
            # 22. RAG FAILED → GEMINI LAST OPTION
            # =============================================

            else:

                st.warning(
                    "Dessert not found in RAG."
                )

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
                        sugar_result[
                            "Confidence"
                        ],
                        "%"
                    )

                    st.caption(
                        sugar_result["Note"]
                    )

                else:

                    st.error(
                        "Could not find or estimate sugar."
                    )


    # =====================================================
    # 23. JSON ERROR
    # =====================================================

    except json.JSONDecodeError:

        st.error(
            "Gemini did not return valid JSON."
        )


    # =====================================================
    # 24. OTHER ERROR
    # =====================================================

    except Exception as error:

        st.error(
            f"An error occurred: {error}"
        )