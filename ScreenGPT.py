from openai import OpenAI
import streamlit as st
import json
import requests

st.set_page_config(initial_sidebar_state="expanded")

#functions

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
    'X-Master-Key': st.secrets["jsonBinKey"]
    }
    st.session_state.data["messages"] = st.session_state.messages
    st.session_state[f"jsonbin_put_response{st.session_state.update_counter}"] = requests.put(url, json=st.session_state.data, headers=headers)

def set_lang(lang):
    if "messages" in st.session_state:
        del st.session_state.messages
    st.session_state.language = lang

def collect_ok():
    st.session_state["collect_status"] = True

#select language
with st.sidebar:
    st.image('./banner.png', use_column_width=True)
    if "language" not in st.session_state:
        st.text('Please select language!')
        col1, col2, blankcol = st.columns([0.25, 0.25, 0.5]) 
        col1.button(label='EN', on_click=set_lang, args=['english'])
        col2.button(label='HU', on_click=set_lang, args=['hungarian'])

#variable definitions
if "data" not in st.session_state:
    st.session_state['data'] = {
        "age" : 0,
        "sex" : "Male",
        "weight" : 0,
        "height" : 0,
    }
if "read_ok" not in st.session_state:
    st.session_state['read_ok'] = False
if "collect_status" not in st.session_state:
    st.session_state['collect_status'] = False
if "readerror" not in st.session_state:
    st.session_state['readerror'] = False
if "show_form" not in st.session_state:
    st.session_state['show_form'] = True
if "sessionID" not in st.session_state:
    st.session_state['sessionID'] = ""


#heading
col_logo, col_head = st.columns([0.2, 0.8])
with col_logo:
    st.image("./logo.png", use_column_width=True)
with col_head:
    st.title("Welcome to ScreenGPT 👨🏽‍⚕️ beta")
    
if "language" in st.session_state:
#load texts
    texts = {}
    with open("./lang.json") as io:
        texts = json.load(io)[st.session_state.language]
    
    with st.sidebar:
    #display read error
        if st.session_state.readerror == True:
                st.write(texts['readeror'])
    #form
        if st.session_state.show_form:    
            with st.form(key='collect_data'):
                st.write(texts["form_header"])
                st.session_state.data["age"] = st.number_input(label=texts['age'])
                st.session_state.data["sex"] = st.selectbox(texts['sex'], [texts['male'], texts['female']])
                st.session_state.data["weight"] = st.number_input(label=texts["weight"])
                st.session_state.data["height"] = st.number_input(label=texts["height"])
                st.markdown(f"<p style='text-align: justify; font-size: 12px'>{texts['disclaimer']}</p>", unsafe_allow_html=True)
                st.form_submit_button(label="OK", on_click=collect_ok)
                if st.session_state.collect_status == True and len(st.session_state.sessionID) == 0:
                    st.write(texts['wait'])
    #load session
        if st.session_state.collect_status == False:
            st.write(texts['askForCode'])
            st.session_state['sessionID'] = st.text_input('ID')
            if len(st.session_state.sessionID) > 0 and st.session_state.read_ok == False:
                if read_from_jsonbin(st.session_state.sessionID):
                    collect_ok()
                st.rerun()
    #chat started
    if st.session_state.collect_status:
        #create openAI class object
        client = OpenAI(api_key=st.secrets["OpenaiKey"])
        #write the sessin ID to sidebar
        if len(st.session_state.sessionID) > 0:
            with st.sidebar:
                st.write(texts['write_ID'])
                st.text(st.session_state.sessionID)
                st.markdown(f"<p style='text-align: justify'>{texts['ID_description']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: justify'>{texts['feedback']}</p>", unsafe_allow_html=True)
                st.link_button(texts['feedback_label'], texts['feedback_url'])
        #create first message
        if "messages" not in st.session_state:            
            st.session_state["messages"] = [{"role": "system", "content": f"{st.secrets['sysprompt_0']} {st.session_state.data['age']} {st.secrets['sysprompt_1']} {st.session_state.data['height']} {st.secrets['sysprompt_2']} {st.session_state.data['weight']} {st.secrets['sysprompt_3']} {st.session_state.language} {st.secrets['sysprompt_4']} {st.session_state.data['sex']} {st.secrets['sysprompt_5']}"}]
            response = client.chat.completions.create(model="gpt-4", temperature=0.2, messages=st.session_state.messages)
            msg = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": msg})
            post_to_jsonbin()
            st.session_state['show_form'] = False
            st.rerun()
        #write out meaasges
        for msg in st.session_state.messages:
            if msg["role"] != "system":
                st.chat_message(msg["role"]).write(msg["content"])
        #input and answer user prompt
        if prompt := st.chat_input():
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            response = client.chat.completions.create(model="gpt-4", temperature=0.2, messages=st.session_state.messages)
            msg = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.chat_message("assistant").write(msg)
            put_to_jsonbin(st.session_state.sessionID)
        #write out session ID under the chat
        st.markdown(f"<p style='text-align: right; font-size: 12px'>Session ID : {st.session_state.sessionID}</p>", unsafe_allow_html=True)

