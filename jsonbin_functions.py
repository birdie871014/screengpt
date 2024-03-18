import streamlit as st
import json
import requests

def post_to_jsonbin():
    url = 'https://api.jsonbin.io/v3/b'
    headers = {
    'Content-Type': 'application/json',
    'X-Master-Key': st.secrets["jsonBinKey"]
    }
    st.session_state.data["messages"] = st.session_state.messages
    
    st.session_state["bin"] = requests.post(url, json=st.session_state.data, headers=headers)
    st.session_state["sessionID"] = st.session_state.bin.json()["metadata"]["id"]

def read_from_jsonbin(id):
    url = f'https://api.jsonbin.io/v3/b/{id}/latest'
    headers = {
    'X-Master-Key': st.secrets["jsonBinKey"]
    }
    response = requests.get(url, json=None, headers=headers)
    if response.status_code == 200:
        st.session_state['read_ok'] = True
        st.session_state['data'] = json.loads(response.text)['record']
        st.session_state['messages'] = st.session_state.data['messages']
        st.session_state['show_form'] = False
        st.session_state['readerror'] = False
        return True
    else: 
        st.session_state['readerror'] = True
        st.session_state['sessionID'] = ""
        return False


def put_to_jsonbin(id):
    if "update_counter" not in st.session_state:
        st.session_state["update_counter"] = 1
    else:
        st.session_state.update_counter += 1
    url = f'https://api.jsonbin.io/v3/b/{id}'
    headers = {
    'Content-Type': 'application/json',
    'X-Master-Key': st.secrets['jsonBinKey']
    }
    st.session_state.data['messages'] = st.session_state.messages
    st.session_state[f"jsonbin_put_response{st.session_state.update_counter}"] = requests.put(url, json=st.session_state.data, headers=headers)
