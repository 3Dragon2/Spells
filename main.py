import streamlit as st
import pandas as pd
import math as m
import re
import json

# Load and prepare data
@st.cache_data
def load_data():
    with open('spells.json') as file:
        data = json.load(file)

    # Define school multipliers (can be customized later)
    school_multipliers = {
        "abjuration": 1.0,
        "conjuration": 1.3,
        "divination": 1.0,
        "enchantment": 1.0,
        "evocation": 1.4,
        "illusion": 0.9,
        "necromancy": 1.1,
        "transmutation": 1.2
    }

    for item in data:
        # Normalize range to integer (in feet where possible)
        raw_range = item.get("range", "")
        match = re.search(r'(\d+)', raw_range)
        range_ft = int(match.group(1)) if match else 0
        item["range_numeric"] = range_ft

        try:
            level = int(item.get("level", 0))
        except:
            level = 0

        school = item.get("school", "").lower()
        multiplier = school_multipliers.get(school, 1.0)

        # New mana cost formula
        #base = round(range_ft / 60) + pow(2, level)
        base = round(level * m.log2(range_ft + 1)) + pow(2, level)
        item["mana cost"] = round(base * multiplier)

    df = pd.json_normalize(data, sep='_')

    # Rename and format
    df.rename(columns={
        'components_verbal': 'Verbal',
        'components_somatic': 'Somatic',
        'components_material': 'Material',
        'components_materials_needed': 'Materials Needed',
        'components_raw': 'Components (Raw)',
        'range_numeric': 'Range (ft)'
    }, inplace=True)

    # Convert bools to emojis
    for col in ['Verbal', 'Somatic', 'Material']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: '✅' if x else '❌')

    # Reorder columns
    preferred_order = ['name', 'level', 'mana cost', 'Range (ft)', 'range', 'duration', 'casting_time']
    remaining_cols = [col for col in df.columns if col not in preferred_order]
    df = df[preferred_order + remaining_cols]

    return df


df = load_data()

# Sidebar filters
st.sidebar.title("Spell Filters")

levels = sorted(df['level'].dropna().unique())
selected_level = st.sidebar.selectbox("Level", options=['All'] + levels)

schools = sorted(df['school'].dropna().unique())
selected_school = st.sidebar.selectbox("School", options=['All'] + schools)

classes = sorted(set(c for sublist in df['classes'].dropna().tolist() for c in (sublist if isinstance(sublist, list) else [sublist])))
selected_class = st.sidebar.selectbox("Class", options=['All'] + classes)

# Filter logic
filtered_df = df.copy()
if selected_level != 'All':
    filtered_df = filtered_df[filtered_df['level'] == selected_level]
if selected_school != 'All':
    filtered_df = filtered_df[filtered_df['school'] == selected_school]
if selected_class != 'All':
    filtered_df = filtered_df[filtered_df['classes'].apply(lambda x: selected_class in x if isinstance(x, list) else False)]

# View mode
view_mode = st.radio("View Mode", ['Table', 'Cards'])

st.title("🧙 Spellbook Viewer")

# Conditional color for mana cost
def color_mana(val):
    if val < 10:
        return 'background-color: #add8e6; color: black'  # light blue + black text
    elif val < 20:
        return 'background-color: #90EE90; color: black'  # light green + black text
    elif val < 40:
        return 'background-color: #FFFFED; color: black'  # light yellow + black text
    elif val < 80:
        return 'background-color: #FFD580; color: black'  # light orange + black text
    else:
        return 'background-color: #FF474C; color: white'  # strong red + white text

if view_mode == 'Table':
    styled_df = filtered_df.style.applymap(color_mana, subset=['mana cost'])
    st.dataframe(styled_df, use_container_width=True, height=600)
else:
    for _, row in filtered_df.iterrows():
        with st.expander(f"{row['name']} ({row['level']} lvl - {row['school']})"):
            st.markdown(f"""
            **Casting Time**: {row['casting_time']}  
            **Range**: {row['range']} ({row['Range (ft)']} ft)  
            **Ritual**: {'✅' if row['ritual'] else '❌'}  
            **Mana Cost**: <span style='background-color:#eef;text-align:center;padding:0.2em 0.4em;border-radius:0.25rem'>{row['mana cost']}</span>  
            **Components**: {row['Components (Raw)']}  
            **Verbal**: {row['Verbal']}  
            **Somatic**: {row['Somatic']}  
            **Material**: {row['Material']}  
            **Materials Needed**: {row['Materials Needed'] or 'None'}  

            <details>
            <summary><strong>Description</strong></summary>
            <p style='white-space: pre-wrap'>{row['description']}</p>
            </details>

            **Higher Levels**: {row['higher_levels'] or 'None'}
            """, unsafe_allow_html=True)

