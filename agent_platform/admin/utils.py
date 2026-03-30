import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_supabase() -> Client:
    return create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["service_key"],
    )
