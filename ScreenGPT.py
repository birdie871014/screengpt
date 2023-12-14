from openai import OpenAI
import streamlit as st
import json

def set_lang(lang):
    if "messages" in st.session_state:
        del st.session_state.messages
    st.session_state.language = lang
    st.session_state["show_form"] = True
def set_collect_status():
    st.session_state["collect_status"] = True
    st.session_state.show_form = False4



st.title("Welcome to ScreenGPT 🧑‍⚕️")
col1, col2, col3, col4 = st.columns([0.4, 0.1, 0.1, 0.4])
col1.text('Please select language!')
col2.button(label='EN', on_click=set_lang, args=['english'])
col3.button(label='HU', on_click=set_lang, args=['hungarian'])


if "language" in st.session_state:
    texts = {}
    with open("./lang.json") as io:
        texts = json.load(io)[st.session_state.language]
    if st.session_state.show_form:
        with st.form(key='collect_data'):
            st.text(texts["form_header"])
            st.session_state["age"] = st.number_input(label=texts['age'])
            st.session_state["sex"] = st.selectbox(texts['sex'], [texts['male'], texts['female']])
            st.session_state["weight"] = st.number_input(label=texts["weight"])
            st.session_state["height"] = st.number_input(label=texts["height"])
            st.form_submit_button(label="OK", on_click=set_collect_status)

    
if "collect_status" in st.session_state:
    if st.session_state.collect_status:
        if "messages" not in st.session_state:
            st.session_state["messages"] = [{"role": "system", "content": f"In this conversation you are the assistant and the user who asks is  {st.session_state.age} years old {st.session_state.height} cm tall {st.session_state.sex} with {st.session_state.weight} kg body weight. Please give personalized answers. In your answer at first evaluate the users parameters and calculate BMI index! You are a healthcare tool. Answer only the questions about lifestyle change!"}]
            st.session_state.messages.append({"role": "assistant", "content": texts["greeting"]})

        
        for msg in st.session_state.messages:
            if msg["role"] != "system":
                st.chat_message(msg["role"]).write(msg["content"])




        if prompt := st.chat_input():
            client = OpenAI(api_key=st.secrets["APIkey"])
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            response = client.chat.completions.create(model="gpt-3.5-turbo", temperature=0.2, messages=st.session_state.messages)
            msg = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.chat_message("assistant").write(msg)


