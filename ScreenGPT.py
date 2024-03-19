from openai import OpenAI
import streamlit as st
import json
from jsonbin_functions import *


st.set_page_config(page_title="ScreenGPT", page_icon='./images/logo.png', menu_items={"About" : "https://www.linkedin.com/company/screengpt/about/"})


#functions


def set_lang(lang):
    if "messages" in st.session_state:
        del st.session_state.messages
    st.session_state.language = lang

def collect_ok():
    if any(v == 0 for v in st.session_state['data'].values()):
        st.warning(texts['zero_value_warning'])
    else:
        st.session_state['collect_status'] = True

#variable definitions
if "data" not in st.session_state:
    st.session_state['data'] = {
        "age" : 0,
        "sex" : 0,
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

st.image("./images/banner.png", use_column_width=True)
st.markdown("<h1 style='color: #5e17eb; text-align: center'>Welcome to ScreenGPT 👨🏽‍⚕️ beta</h1>", unsafe_allow_html=True)
with st.sidebar:
    st.image("./images/logo.png", use_column_width=True)

#select language

if "language" not in st.session_state:
    col1, col2, col3, col4 = st.columns([0.4, 0.1, 0.1, 0.4])
    col1.write('Please select language!')
    col2.button(label='🇬🇧', on_click=set_lang, args=['english'])
    col3.button(label='🇭🇺', on_click=set_lang, args=['hungarian'])


if "language" in st.session_state:
#load texts
    texts = {}
    with open("./lang.json") as io:
        texts = json.load(io)[st.session_state.language]
    
#display read error
    if st.session_state.readerror == True:
            st.write(texts['readeror'])
#form
    
    if st.session_state.show_form:    
        with st.form(key='collect_data'):
            st.write(texts["form_header"])
            st.session_state.data["age"] = st.number_input(label=texts['age'], min_value=0, step=1)
            st.session_state.data["sex"] = st.selectbox(texts['sex'], [texts['male'], texts['female']])
            st.session_state.data["weight"] = st.number_input(label=texts["weight"], min_value=0, step=1)
            st.session_state.data["height"] = st.number_input(label=texts["height"], min_value=0, step=1)
            st.markdown(f"<p style='text-align: justify; font-size: 12px'>{texts['disclaimer']}</p>", unsafe_allow_html=True)
            submit = st.form_submit_button(label="OK")
            if st.session_state.collect_status == True and len(st.session_state.sessionID) == 0:
                st.write(texts['wait'])
        if submit:
            collect_ok()
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
            st.session_state["messages"] = [{"role": "system", "content": st.secrets['lifestyle_sysprompt'].format(st.session_state.data['age'], st.session_state.data['height'], st.session_state.data['weight'], st.session_state.language, st.session_state.data['sex'])}]
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
        st.markdown(f"""<div style='border: 2px solid blue; border-radius: 10px; color: white; background-color: blue; position: fixed; bottom: 128px; right: 30%'>
                            <p style='margin-bottom: 0; color: white; text-align: right; font-size: 12px'>&#160;&#160;&#160; Session ID : {st.session_state.sessionID} &#160;&#160;&#160;</p>
                        </div>""", unsafe_allow_html=True)

#linkedin logo        
with st.sidebar:
    st.markdown("""
                <div style="text-align: center; height: 80px; width:120px;  position: fixed; bottom: 20px; background-color: rgba(255,255,255,0.5); border: 0px; border-radius: 20px">
                    <p style="margin-bottom: 0; color: black">Follow Us!</p>
                    <a href='https://www.linkedin.com/company/screengpt/about/'>
                        <img src='https://logos-world.net/wp-content/uploads/2020/05/Linkedin-Logo.png', alt='follow us on Linkedin', border=0, width=100px>
                    </a>
                </div>
                """, unsafe_allow_html=True)