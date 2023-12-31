from openai import OpenAI
import streamlit as st
import json
import requests


def post_to_jsonbin():
    url = 'https://api.jsonbin.io/v3/b'
    headers = {
    'Content-Type': 'application/json',
    'X-Master-Key': st.secrets["jsonBinKey"]
    }
    st.session_state.data = {
        "age" : st.session_state.age,
        "sex" : st.session_state.sex,
        "weight" : st.session_state.weight,
        "height" : st.session_state.height,
        "messages" : st.session_state.messages
    }
    st.session_state["bin"] = requests.post(url, json=st.session_state.data, headers=headers)

def put_to_jsonbin():
    if "update_counter" not in st.session_state:
        st.session_state["update_counter"] = 1
    else:
        st.session_state.update_counter += 1
    url = f'https://api.jsonbin.io/v3/b/{st.session_state.bin.json()["metadata"]["id"]}'
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
    st.session_state["collect_status"] = False

def collect_ok():
    st.session_state["collect_status"] = True


st.title("Welcome to ScreenGPT 👨🏽‍⚕️")

col1, col2, col3, col4 = st.columns([0.4, 0.1, 0.1, 0.4])
col1.text('Please select language!')
col2.button(label='EN', on_click=set_lang, args=['english'])
col3.button(label='HU', on_click=set_lang, args=['hungarian'])


if "language" in st.session_state:
    texts = {}
    with open("./lang.json") as io:
        texts = json.load(io)[st.session_state.language]
    with st.form(key='collect_data', ):
        st.text(texts["form_header"])
        st.session_state["age"] = st.number_input(label=texts['age'])
        st.session_state["sex"] = st.selectbox(texts['sex'], [texts['male'], texts['female']])
        st.session_state["weight"] = st.number_input(label=texts["weight"])
        st.session_state["height"] = st.number_input(label=texts["height"])
        st.form_submit_button(label="OK", on_click=collect_ok)

    
if "collect_status" in st.session_state:
    client = OpenAI(api_key=st.secrets["OpenaiKey"])
    if st.session_state.collect_status:
        if "messages" not in st.session_state:            
            st.session_state["messages"] = [{"role": "system", "content": f"In this conversation you are the assistant developed for assist lifestyle change. At first introduce yourself. The user who asks is {st.session_state.age} years old {st.session_state.height} cm tall and has {st.session_state.weight} kg body weight. The language of this conversation is {st.session_state.language}. The gender of the user in the language of the conversation is '{st.session_state.sex}'. Please give personalized answers, and allways note the gender. In your answer evaluate users BMI index! If it is out of the normal range, give an advice how to reach the ideal body weight. You are a healthcare tool. Answer only the questions about lifestyle change!"}]
            response = client.chat.completions.create(model="gpt-4", temperature=0.2, messages=st.session_state.messages)
            msg = response.choices[0].message.content
            #msg = st.session_state.sex + " " + str(st.session_state.age) + " " + str(st.session_state.height) + " " + str(st.session_state.weight)
            st.session_state.messages.append({"role": "assistant", "content": msg})
            post_to_jsonbin()
        
        for msg in st.session_state.messages:
            if msg["role"] != "system":
                st.chat_message(msg["role"]).write(msg["content"])
        

        if prompt := st.chat_input():
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            response = client.chat.completions.create(model="gpt-4", temperature=0.2, messages=st.session_state.messages)
            msg = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.chat_message("assistant").write(msg)
            put_to_jsonbin()



