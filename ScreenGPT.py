from openai import OpenAI
import streamlit as st
import json
import requests


st.set_page_config(page_title="ScreenGPT", page_icon='./images/logo.png', menu_items={"About" : "https://www.linkedin.com/company/screengpt/about/"})

st.image("./images/banner.png", use_column_width=True)
with st.sidebar:
    st.image("./images/logo.png", use_column_width=True)        
    st.markdown("""
                <div style="text-align: center; height: 40px; width:120px;  position: fixed; bottom: 20px">
                    <a href='https://www.linkedin.com/company/screengpt/about/'>
                        <img src='https://logos-world.net/wp-content/uploads/2020/05/Linkedin-Logo.png', alt='follow us on Linkedin', border=0, width=100px>
                    </a>
                </div>
                """, unsafe_allow_html=True)
if "started" not in st.session_state:
    st.session_state.started = False

if "key" not in st.session_state:
    st.session_state.key = ""

if "stat_data" not in st.session_state:
    st.session_state['stat_data'] = {}

if "jb_headers" not in st.session_state:
    st.session_state.jb_headers = {'Content-Type': 'application/json', 'X-Master-Key': st.secrets["jsonBinKey"]}
        
def load_lang(lang):
    with open("./lang.json") as io:
        st.session_state.texts = json.load(io)[lang]
        st.session_state.language = lang
        st.session_state.started = True
def select_topic(topic):
    st.session_state.messages.append({"role" : "user", "content" : st.session_state.texts['first_user_prompt'].format(topic)})
    if topic == st.session_state.texts['lifestyle']:
        with open("./system_prompts.json") as io:
            st.session_state.system_prompts = json.load(io)['lifestyle']
    if topic == st.session_state.texts['cervical']:
        with open("./system_prompts.json") as io:
            st.session_state.system_prompts = json.load(io)['cervical']
    st.session_state.messages.append({"role" : "system", "content" : st.session_state.system_prompts['structure'] + st.session_state.system_prompts['init'].format(st.session_state.language)})
    st.session_state.nav_keys = list(st.session_state.system_prompts.keys())[3:-1]
def load_session(id):
    url = f'https://api.jsonbin.io/v3/b/{id}/latest'
    headers = {
    'X-Master-Key': st.secrets["jsonBinKey"]
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()['record']
        st.session_state['messages'] = data['messages']
        load_lang(data['language'])
        return True
    else: 
        st.error("An error occurred while loading session")
        st.session_state['sessionID'] = ""
        return False
def choose_option(option, index):
    if actual_data['next_key'] == 'inOption':
        st.session_state['key'] = actual_data[option]['next_key']
        st.session_state.messages.append({"role" : "system", "content" : actual_data[option]['sysprompt'] + actual_data[option]['question']})
    else:
        st.session_state['key'] = actual_data['next_key']
        st.session_state.messages.append({"role" : "system", "content" : actual_data[option]['sysprompt'] + actual_data['question']})
    st.session_state.messages.append({"role" : "user", "content" : actual_data['options'][st.session_state['language']][index]})
    for key in actual_data[option]['stat_data'].keys():
        st.session_state.stat_data[key] = actual_data[option]['stat_data'][key]
    wait_info = st.info(st.session_state.texts['wait'])
    response = client.chat.completions.create(model="gpt-4", temperature=0.6, messages=st.session_state.messages)
    wait_info.empty()
    msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": msg})
    requests.put(url=f'https://api.jsonbin.io/v3/b/{st.session_state.sessionID}', json={"language" : st.session_state.language, "messages" : st.session_state.messages, "stat_data" : st.session_state["stat_data"]}, headers=st.session_state.jb_headers)

if not st.session_state.started:
    st.markdown("<h1 style='color: #5e17eb; text-align: center'>Welcome to ScreenGPT 👨🏽‍⚕️ beta! <br> Please select language!</h1>", unsafe_allow_html=True)
    col0, col1, col2, col3= st.columns([0.3, 0.2, 0.2, 0.3])
    col1.button("English", on_click=load_lang, kwargs={"lang" : "english"}, use_container_width=True)
    col2.button("Hungarian", on_click=load_lang, kwargs={"lang" : "hungarian"}, use_container_width=True)
    st.markdown(f"<h3 style='color: #5e17eb; text-align: center'>or <br> If you want to resume a previous session, you can enter the ID here.</h1>", unsafe_allow_html=True)
    st.session_state['sessionID'] = st.text_input('ID', label_visibility="hidden")
    if len(st.session_state.sessionID) > 0:
        loaded = load_session(st.session_state.sessionID)
        if loaded:
            st.rerun()

if st.session_state.started:
    client = OpenAI(api_key=st.secrets["OpenaiKey"])
    if "messages" not in st.session_state:
        st.session_state['messages'] = [{"role" : "assistant", "content" : st.session_state.texts['greeting']}]
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            st.chat_message(msg["role"]).write(msg["content"])
    if len(st.session_state.messages) == 1:
        select_topic(st.session_state.texts['cervical'])
        #col0, col1 = st.columns([0.6, 0.4])
        #col1.button(st.session_state.texts['lifestyle'], on_click=select_topic, kwargs={"topic" : st.session_state.texts['lifestyle']}, use_container_width=True)
        #col1.button(st.session_state.texts['cervical'], on_click=select_topic, kwargs={"topic" : st.session_state.texts['cervical']}, use_container_width=True)
        st.rerun()
    elif len(st.session_state.messages) == 3:
        wait_info = st.info(st.session_state.texts['wait'])
        response = client.chat.completions.create(model="gpt-4", temperature=0.3, messages=st.session_state.messages)
        wait_info.empty()
        ans = json.loads(response.choices[0].message.content)
        msg = ans['message']
        st.session_state['key'] = ans['key']
        st.session_state.messages.append({"role": "assistant", "content": msg})
        response = requests.post(url='https://api.jsonbin.io/v3/b', json={"language" : st.session_state.language, "messages" : st.session_state.messages}, headers=st.session_state.jb_headers)        
        st.session_state.sessionID = response.json()["metadata"]["id"]
        st.rerun()
    else:
        with st.sidebar:
                st.write(st.session_state.texts['write_ID'])
                st.text(st.session_state.sessionID)
                st.markdown(f"<p style='text-align: justify'>{st.session_state.texts['ID_description']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: justify'>{st.session_state.texts['feedback']}</p>", unsafe_allow_html=True)
                st.link_button(st.session_state.texts['feedback_label'], st.session_state.texts['feedback_url'])
        if st.session_state['key'] in st.session_state.nav_keys:
            actual_data = st.session_state.system_prompts[st.session_state['key']]
            for i in range(len(actual_data['options']['keys'])):
                st.button(actual_data['options'][st.session_state['language']][i],on_click=choose_option, kwargs={"option" : actual_data['options']['keys'][i], "index" : i}, use_container_width=True)
        else:
            if prompt := st.chat_input():
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.chat_message("user").write(prompt)
                if st.session_state['key'] == 'gender_select':
                    sysprompt = {"role": "system", "content": st.session_state.system_prompts['structure'] + st.session_state.system_prompts['gender_select']} 
                    st.session_state.messages.append(sysprompt)
                elif st.session_state['key'] == 'end':
                    sysprompt = {"role": "system", "content": st.session_state.system_prompts['end']} 
                    st.session_state.messages.append(sysprompt)
                    st.session_state['key'] = 'free_conversation'
                wait_info = st.info(st.session_state.texts['wait'])
                response = client.chat.completions.create(model="gpt-4", temperature=0.6, messages=st.session_state.messages)
                wait_info.empty()
                try:
                    ans = json.loads(response.choices[0].message.content)
                    msg = ans['message']
                    st.session_state['key'] = ans['key']
                    for key in ans['stat_data'].keys():
                        st.session_state['stat_data'][key] = ans['stat_data'][key]
                except:
                    msg = response.choices[0].message.content
                            
                st.session_state.messages.append({"role": "assistant", "content": msg})
                st.chat_message("assistant").write(msg)
                requests.put(url=f'https://api.jsonbin.io/v3/b/{st.session_state.sessionID}', json={"language" : st.session_state.language, "messages" : st.session_state.messages, "stat_data" : st.session_state["stat_data"]}, headers=st.session_state.jb_headers)
                st.rerun()
            