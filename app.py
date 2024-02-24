import streamlit as st


hide_streamlit_style = """
<style>
    #MainMenu {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    [data-testid="stSidebarNav"] {visibility: hidden;}
    [data-testid="stSidebarNav"] [data-testid="stSidebarNavItems"] {max-height: 0;}
    [data-testid="stSidebarNav"] [data-testid="stSidebarNavItems"] li  {display: none;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

print("app")
st.write("Hello Streamlit World!")

st.sidebar.write("test")

