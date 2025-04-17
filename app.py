from collections import defaultdict
import pandas as pd
import streamlit as st
import os

from spreadsheets import save_dataframe_to_spreadsheet, spreadsheet_to_dict, CREDENTIALS_FILE, spreadsheet_to_pandas

VALID_EXTENSIONS = (".json")


def check_for_credentials(uploaded_files):
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name
            os.makedirs("files", exist_ok=True)
            if file_name.endswith(".json"):
                with open(CREDENTIALS_FILE, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                    st.rerun()


def get_ingredient(food_name):
    return st.session_state.recetas[food_name].dropna().to_dict()


def load_menu():
    if "menu" not in st.session_state:
        st.session_state.menu = {i["dia"]: i["comida"] for i in spreadsheet_to_dict('menu')}
    if "recetas" not in st.session_state:
        recetas = spreadsheet_to_pandas('recetas')
        recetas = recetas.set_index('ingredientes')
        st.session_state.recetas = recetas
    if 'lugar' not in st.session_state:
        lugar = spreadsheet_to_pandas('lugar')
        st.session_state.lugar = {col: lugar[col].dropna().tolist() for col in lugar.columns}
    if 'all_food_names' not in st.session_state:
        st.session_state.all_food_names = list(st.session_state.recetas.columns)


def show_weekday_menu():
    for day, food_name in st.session_state.menu.items():
        col1, col2, col3 = st.columns([0.9, 2, 1])
        with col1:
            st.markdown(f'### {day}')
        with col2:
            with st.expander(f'{food_name}'):
                for ingredient_name, quantity in get_ingredient(food_name).items():
                    st.checkbox(f"{ingredient_name}    ->    {quantity}", key=f'checkbox-{day}-{ingredient_name}')

        with col3:
            with st.expander("Cambiar comida"):
                st.selectbox("Selecciona nueva comida", st.session_state.all_food_names, key=f'selectbox-{day}')
                if st.button("Guardar", key=f'button-{day}'):
                    st.session_state.menu[day] = st.session_state[f'selectbox-{day}']
                    st.rerun()


def sort_by_shopping_place(ingredients):
    sorted_ingredients = defaultdict(dict)
    for ingredient_name, quantity in ingredients.items():
        for place, items in st.session_state.lugar.items():
            if ingredient_name in items:
                sorted_ingredients[place][ingredient_name] = round(quantity, 1)
    return sorted_ingredients


def create_shopping_list():
    ingredients = defaultdict(int)
    for day, food_name in st.session_state.menu.items():
        for ingredient_name, quantity in get_ingredient(food_name).items():
            ingredients[ingredient_name] += float(quantity)

    sorted_ingredients = sort_by_shopping_place(ingredients)
    for place, items in sorted_ingredients.items():
        with st.expander(place):
            for k, v in items.items():
                st.checkbox(f"{k}    ->    {v}", key=f'checkbox-{k}')



def save_weekday_menu():
    if st.button("Guardar menu"):
        save_dataframe_to_spreadsheet('menu', pd.DataFrame(st.session_state.menu.items(), columns=['dia', 'comida']))
        st.success("Menu guardado!")
        print(st.session_state.menu)


if os.path.exists(CREDENTIALS_FILE):
    load_menu()
    st.markdown("# Menu semanal")
    show_weekday_menu()
    save_weekday_menu()
    st.markdown("# Lista de compras")
    create_shopping_list()
else:
    st.markdown("# Configuracion de credenciales")
    if uploaded_files := st.file_uploader("Subi tu json de credenciales", type=VALID_EXTENSIONS, accept_multiple_files=True):
        check_for_credentials(uploaded_files)
    
