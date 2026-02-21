import streamlit as st
import pandas as pd

st.set_page_config(page_title="Market Basket Recommender", page_icon="🛒", layout="wide")

# -----------------------------
# Load Rules
# -----------------------------
@st.cache_data
def load_rules():
    df = pd.read_csv("strong_rules.csv")
    return df

strong_rules = load_rules()

# -----------------------------
# Parse antecedents/consequents
# -----------------------------
def _parse_set_row(row, col_name, alt_col_name=None):
    cell = row.get(col_name, None)
    try:
        if pd.notna(cell):
            fs = eval(cell)
            return set(str(x).strip().upper() for x in fs)
    except Exception:
        pass
    if alt_col_name and alt_col_name in row and pd.notna(row[alt_col_name]):
        return set(s.strip().upper() for s in str(row[alt_col_name]).split("|") if s.strip())
    return set()

strong_rules['antecedents_set'] = strong_rules.apply(
    lambda r: _parse_set_row(r, 'antecedents', 'antecedents_str'), axis=1)

strong_rules['consequents_set'] = strong_rules.apply(
    lambda r: _parse_set_row(r, 'consequents', 'consequents_str'), axis=1)

# -----------------------------
# Recommendation Function (Multi-select)
# -----------------------------
def recommend_items(selected_items, rules_df, top_n=5):

    selected_items = [item.strip().upper() for item in selected_items]
    recommendations = []

    for item in selected_items:
        matched = rules_df[rules_df['antecedents_set'].apply(lambda s: item in s)]

        matched = matched.sort_values(
            ['confidence', 'lift'], ascending=False
        )

        for _, row in matched.iterrows():
            for product in row['consequents_set']:
                if product not in selected_items:
                    score = row['confidence'] * row['lift']
                    recommendations.append((product, score, row['confidence'], row['lift']))

    recommendations = sorted(recommendations, key=lambda x: x[1], reverse=True)

    final = []
    seen = set()

    for product, score, conf, lift in recommendations:
        if product not in seen:
            final.append((product, conf, lift))
            seen.add(product)

    return final[:top_n]


# -----------------------------
# UI
# -----------------------------
st.title("🛒 Smart Market Basket Recommendation System")
st.markdown("### Discover products customers buy together")

col1, col2 = st.columns([2, 1])

with col1:
    product_list = sorted({
        item for row in strong_rules['antecedents_set'] for item in row
    })

    selected_products = st.multiselect(
        "Select products you bought:",
        product_list
    )

with col2:
    top_n = st.slider("Number of Recommendations", 1, 10, 5)

st.divider()

if st.button("✨ Get Recommendations"):

    if selected_products:
        results = recommend_items(selected_products, strong_rules, top_n)

        if results:
            st.subheader("🎯 Recommended Products")

            for i, (item, conf, lift) in enumerate(results, 1):
                with st.container():
                    st.markdown(f"### {i}. {item}")
                    st.write(f"Confidence: {round(conf, 2)}")
                    st.write(f"Lift: {round(lift, 2)}")
                    st.progress(min(conf, 1.0))
                    st.divider()
        else:
            st.warning("No strong recommendations found for this combination 😅")

    else:
        st.info("Please select at least one product.")