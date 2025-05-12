import streamlit as st
import pandas as pd
import json

# Load and prepare data
@st.cache_data
def load_data():
    with open('spells.json') as file:
        data = json.load(file)

    # Add mana cost based on level
    for item in data:
        if "level" in item:
            try:
                level = int(item["level"])
                item["mana cost"] = (level + 1) * 15
            except:
                item["mana cost"] = 0

    df = pd.json_normalize(data, sep='_')

    # Rename and format
    df.rename(columns={
        'components_verbal': 'Verbal',
        'components_somatic': 'Somatic',
        'components_material': 'Material',
        'components_materials_needed': 'Materials Needed',
        'components_raw': 'Components (Raw)'
    }, inplace=True)

    # Convert bools to emojis
    for col in ['Verbal', 'Somatic', 'Material']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: '✅' if x else '❌')

    # Reorder columns
    preferred_order = ['name', 'level', 'mana cost', 'range', 'duration', 'casting_time']
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

if view_mode == 'Table':
    st.dataframe(filtered_df, use_container_width=True)
else:
    for _, row in filtered_df.iterrows():
        with st.expander(f"{row['name']} ({row['level']} lvl - {row['school']})"):
            st.markdown(f"""
            **Casting Time**: {row['casting_time']}  
            **Range**: {row['range']}  
            **Ritual**: {'✅' if row['ritual'] else '❌'}  
            **Mana Cost**: {row['mana cost']}  
            **Components**: {row['Components (Raw)']}  
            **Verbal**: {row['Verbal']}  
            **Somatic**: {row['Somatic']}  
            **Material**: {row['Material']}  
            **Materials Needed**: {row['Materials Needed'] or 'None'}  
            
            **Description**: {row['description']}  
            **Higher Levels**: {row['higher_levels'] or 'None'}
            """)
