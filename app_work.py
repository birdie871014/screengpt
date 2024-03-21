from openai import OpenAI
import streamlit as st
import json
import requests


st.set_page_config(page_title="ScreenGPT", page_icon='./images/logo.png', menu_items={"About" : "https://www.linkedin.com/company/screengpt/about/"})

st.image("./images/banner.png", use_column_width=True)

if "jb_headers" not in st.session_state:
    st.session_state.jb_headers = {'Content-Type': 'application/json', 'X-Master-Key': st.secrets["jsonBinKey"]}

with open("./lang.json") as io:
        st.session_state.texts = json.load(io)["english"]
ID = "65fc4830dc74654018b635da"
st.session_state.system_prompts = requests.get(url=f"https://api.jsonbin.io/v3/b/{ID}/latest", headers=st.session_state.jb_headers).json()['record']['cervical']

def put_to_jsonbin():
    requests.put(url=f"https://api.jsonbin.io/v3/b/{ID}", json={"cervical" : st.session_state.system_prompts}, headers=st.session_state.jb_headers)

with st.sidebar:
    with st.form('system prompts'):
        for key in st.session_state.system_prompts.keys():
            st.session_state.system_prompts[key] = st.text_area(f'prompt key: {key}', value=st.session_state.system_prompts[key])
        st.form_submit_button("SAVE", on_click=put_to_jsonbin)

st.markdown("<h1 style='color: #5e17eb; text-align: center'>Welcome to ScreenGPT 👨🏽‍⚕️ <br> work version for cervical cacncer prevention topic</h1>", unsafe_allow_html=True)



client = OpenAI(api_key=st.secrets["OpenaiKey"])
if "messages" not in st.session_state:
    st.session_state['messages'] = [{"role" : "assistant", "content" : st.session_state.texts['greeting']}, {"role" : "user", "content" : "The topic i would like to talk about is the cervical cancer prevention."}, {"role" : "system", "content" : st.session_state.system_prompts['init']}]
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])
    response = client.chat.completions.create(model="gpt-4", temperature=0.2, messages=st.session_state.messages)
    msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
else:
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])
  
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    if len(st.session_state.messages) == 5:
        sysprompt = {"role": "system", "content": st.session_state.system_prompts['1']} 
    elif len(st.session_state.messages) == 8:
        sysprompt = {"role": "system", "content": st.session_state.system_prompts['2']}
    elif len(st.session_state.messages) == 11:
        sysprompt = {"role": "system", "content": st.session_state.system_prompts['3']}
    elif len(st.session_state.messages) == 14:
        sysprompt = {"role": "system", "content": st.session_state.system_prompts['4']}
    st.session_state.messages.append(sysprompt)
    st.chat_message("system").write(sysprompt)
    response = client.chat.completions.create(model="gpt-4", temperature=0.3, messages=st.session_state.messages)
    msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
        
        
        