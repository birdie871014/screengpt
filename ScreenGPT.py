from openai import OpenAI
import streamlit as st
import json
import requests


st.set_page_config(page_title="ScreenGPT", page_icon='./images/logo.png', menu_items={"About" : "https://www.linkedin.com/company/screengpt/about/"})

st.image("./images/banner.png", use_column_width=True)
with st.sidebar:
    st.image("./images/logo.png", use_column_width=True)        
    st.markdown("""
                <div style="text-align: center; height: 80px; width:120px;  position: fixed; bottom: 20px; background-color: rgba(255,255,255,0.5); border: 0px; border-radius: 20px">
                    <p style="margin-bottom: 0; color: black">Follow Us!</p>
                    <a href='https://www.linkedin.com/company/screengpt/about/'>
                        <img src='https://logos-world.net/wp-content/uploads/2020/05/Linkedin-Logo.png', alt='follow us on Linkedin', border=0, width=100px>
                    </a>
                </div>
                """, unsafe_allow_html=True)
if "lang_selected" not in st.session_state:
    st.session_state.lang_selected = False
if "jb_headers" not in st.session_state:
    st.session_state.jb_headers = {'Content-Type': 'application/json', 'X-Master-Key': st.secrets["jsonBinKey"]}
        
def load_lang(lang):
    with open("./lang.json") as io:
        st.session_state.texts = json.load(io)[lang]
        st.session_state.lang_selected = True
def select_topic(topic):
    st.session_state.messages.append({"role" : "user", "content" : st.session_state.texts['first_user_prompt'].format(topic)})
    if topic == st.session_state.texts['lifestyle']:
        with open("./system_prompts.json") as io:
            st.session_state.system_prompts = json.load(io)['lifestyle']
    if topic == st.session_state.texts['cervical']:
        with open("./system_prompts.json") as io:
            st.session_state.system_prompts = json.load(io)['cervical']
    st.session_state.messages.append({"role" : "system", "content" : st.session_state.system_prompts['init']})
        

if not st.session_state.lang_selected:
    st.markdown("<h1 style='color: #5e17eb; text-align: center'>Welcome to ScreenGPT 👨🏽‍⚕️ beta! <br> Please select language!</h1>", unsafe_allow_html=True)
    col0, col1, col2, col3= st.columns([0.3, 0.2, 0.2, 0.3])
    col1.button("English", on_click=load_lang, kwargs={"lang" : "english"})
    col2.button("Hungarian", on_click=load_lang, kwargs={"lang" : "hungarian"})
if st.session_state.lang_selected:
    client = OpenAI(api_key=st.secrets["OpenaiKey"])
    if "messages" not in st.session_state:
        st.session_state['messages'] = [{"role" : "assistant", "content" : st.session_state.texts['greeting']}]
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            st.chat_message(msg["role"]).write(msg["content"])
    if len(st.session_state.messages) == 1:
        col0, col1, col2 = st.columns([0.2, 0.4, 0.4])
        col1.button(st.session_state.texts['lifestyle'], on_click=select_topic, kwargs={"topic" : st.session_state.texts['lifestyle']})
        col2.button(st.session_state.texts['cervical'], on_click=select_topic, kwargs={"topic" : st.session_state.texts['cervical']})
    elif len(st.session_state.messages) == 3:
        response = client.chat.completions.create(model="gpt-4", temperature=0.2, messages=st.session_state.messages)
        msg = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": msg})
        response = requests.post(url='https://api.jsonbin.io/v3/b', json=st.session_state.messages, headers=st.session_state.jb_headers)        
        st.session_state.sessionID = response.json()["metadata"]["id"]
        st.rerun()
    else:
        if prompt := st.chat_input():
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            if len(st.session_state.messages) == 4:
                st.session_state.messages.append({"role": "system", "content": st.session_state.system_prompts['ans_1']})
            response = client.chat.completions.create(model="gpt-4", temperature=0.3, messages=st.session_state.messages)
            msg = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.chat_message("assistant").write(msg)
            requests.put(url=f'https://api.jsonbin.io/v3/b/{st.session_state.sessionID}', json=st.session_state.messages, headers=st.session_state.jb_headers)