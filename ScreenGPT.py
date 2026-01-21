from openai import OpenAI
import streamlit as st
import json
import requests
from datetime import datetime
from pydantic import BaseModel
from typing import Literal, Optional, Dict, Any


# Pydantic models for structured outputs
class NavigationResponse(BaseModel):
    message: str
    next_state: str
    collected_data: Optional[Dict[str, Any]] = None


st.set_page_config(
    page_title="ScreenGPT 2.0", 
    page_icon='./images/logo.png', 
    menu_items={"About": "https://www.linkedin.com/company/screengpt/about/"}
)

st.image("./images/banner.png", use_container_width=True)

with st.sidebar:
    st.image("./images/logo.png", use_container_width=True)
    st.markdown("<h1 style='color: #5e17eb'>created by</h1>", unsafe_allow_html=True)
    st.markdown("""
                <p style="text-align: center; margin-bottom: 0px; font-family: serif; font-size: 20px"> 
                <a href="https://www.linkedin.com/in/viola-angyal/">Angyal Viola</a>
                </p>
                <p style="text-align: center; margin-bottom: 0px; font-family: serif; font-size: 20px"> 
                <a href="https://www.linkedin.com/in/%C3%A1d%C3%A1m-dr-bertalan-613805241/">Bertalan Ádám</a>
                </p>
                <p style="text-align: center; margin-bottom: 0px; font-family: serif; font-size: 20px"> 
                <a href="https://www.linkedin.com/in/kiss-tilla-bianka">Kiss Tilla Bianka</a>
                </p>
                <p style="text-align: center; margin-bottom: 30px; font-family: serif; font-size: 20px"> 
                <a href="https://doktori.hu/index.php?menuid=192&lang=HU&sz_ID=9155">Dinya Elek</a>
                </p>
                """, unsafe_allow_html=True)
    blank1, logo, blank2 = st.columns(3)
    logo.image("./images/Semmelweis_logo_Latin_BLACK_PNG.png")        
    st.markdown("""
                <div style="text-align: center; height: 40px; width:120px; position: fixed; bottom: 20px">
                    <a href='https://www.linkedin.com/company/screengpt/about/'>
                        <img src='https://logos-world.net/wp-content/uploads/2020/05/Linkedin-Logo.png', alt='follow us on Linkedin', border=0, width=100px>
                    </a>
                </div>
                """, unsafe_allow_html=True)


# Initialize session state
if "started" not in st.session_state:
    st.session_state.started = False

if "nav_params" not in st.session_state:
    with open("./navigation_parameters.json") as f:
        st.session_state.nav_params = json.load(f)

if "current_state" not in st.session_state:
    st.session_state.current_state = None

if "current_flow" not in st.session_state:
    st.session_state.current_flow = None

if "stat_data" not in st.session_state:
    st.session_state.stat_data = {
        'resp_times': [],
        'collected_data': {}
    }

if "sessionID" not in st.session_state:
    st.session_state.sessionID = ""


def load_lang(lang):
    """Load language configuration"""
    with open("./lang.json") as io:
        st.session_state.texts = json.load(io)[lang]
        st.session_state.language = lang
        st.session_state.started = True


def save_session():
    """Save session data to remote JSON server"""
    session_data = {
        "language": st.session_state.language,
        "messages": st.session_state.messages,
        "stat_data": st.session_state.stat_data,
        "current_state": st.session_state.current_state,
        "current_flow": st.session_state.current_flow,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        if st.session_state.sessionID:
            # Update existing session
            url = f'https://birdies-json.ddns.net/sessions/{st.session_state.sessionID}'
            response = requests.put(url, json=session_data)
        else:
            # Create new session
            url = 'https://birdies-json.ddns.net/sessions'
            response = requests.post(url, json=session_data)
            if response.status_code in [200, 201]:
                data = response.json()
                st.session_state.sessionID = data.get('id', '')
        
        return response.status_code in [200, 201]
    except Exception as e:
        st.error(f"Error saving session: {str(e)}")
        return False


def load_session(session_id):
    """Load session data from remote JSON server"""
    try:
        url = f'https://birdies-json.ddns.net/sessions/{session_id}'
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.messages = data.get('messages', [])
            st.session_state.stat_data = data.get('stat_data', {'resp_times': [], 'collected_data': {}})
            st.session_state.current_state = data.get('current_state')
            st.session_state.current_flow = data.get('current_flow')
            load_lang(data.get('language', 'english'))
            return True
        else:
            st.error("Session not found")
            return False
    except Exception as e:
        st.error(f"Error loading session: {str(e)}")
        return False


def get_message_text(message_key):
    """Get message text in current language"""
    messages = st.session_state.nav_params.get('messages', {})
    if message_key in messages:
        return messages[message_key].get(st.session_state.language, messages[message_key].get('english', ''))
    return message_key


def get_option_set(option_set_key):
    """Get option set in current language"""
    option_sets = st.session_state.nav_params.get('option_sets', {})
    if option_set_key in option_sets:
        option_set = option_sets[option_set_key]
        return {
            'keys': option_set.get('keys', []),
            'labels': option_set.get(st.session_state.language, option_set.get('english', []))
        }
    return {'keys': [], 'labels': []}


def evaluate_router(router_key, user_data):
    """Evaluate router rules and return next state"""
    routers = st.session_state.nav_params.get('routers', {})
    if router_key not in routers:
        return None
    
    router = routers[router_key]
    rules = router.get('rules', [])
    
    for rule in rules:
        conditions = rule.get('if', {})
        match = True
        
        for key, value in conditions.items():
            if key == 'gender':
                if user_data.get('gender') != value:
                    match = False
                    break
            elif key == 'age_lt':
                if user_data.get('age', 100) >= value:
                    match = False
                    break
            elif key == 'age_gt':
                if user_data.get('age', 0) <= value:
                    match = False
                    break
            elif key == 'age_between':
                age = user_data.get('age', 0)
                if not (value[0] <= age <= value[1]):
                    match = False
                    break
            elif key in user_data:
                if user_data[key] != value:
                    match = False
                    break
            elif key == 'last_choice':
                if user_data.get('last_choice') != value:
                    match = False
                    break
        
        if match:
            return rule.get('goto')
    
    return None


def generate_ai_response(system_prompt, user_message=None, include_language=True):
    """Generate AI response using OpenAI with structured outputs"""
    client = OpenAI(api_key=st.secrets["OpenaiKey"])
    
    messages = st.session_state.messages.copy()
    
    # Add language context to system prompt
    if include_language and system_prompt:
        lang_name = "Hungarian" if st.session_state.language == "hungarian" else "English"
        system_prompt = f"{system_prompt} You must respond in {lang_name}. All your responses should be in {lang_name} language."
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if user_message:
        messages.append({"role": "user", "content": user_message})
    
    start_time = datetime.now()
    wait_info = st.info(st.session_state.texts.get('wait', 'Please wait...'))
    
    try:
        # Using gpt-4o-mini (gpt-5-mini doesn't exist yet)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.6,
            messages=messages
        )
        
        wait_info.empty()
        end_time = datetime.now()
        st.session_state.stat_data['resp_times'].append((end_time - start_time).total_seconds())
        
        return response.choices[0].message.content
    except Exception as e:
        wait_info.empty()
        st.error(f"Error generating response: {str(e)}")
        return None


def select_flow(flow_name):
    """Initialize a conversation flow"""
    flows = st.session_state.nav_params.get('flows', {})
    if flow_name in flows:
        flow = flows[flow_name]
        st.session_state.current_flow = flow_name
        st.session_state.current_state = flow.get('entry')
        
        # Initialize with flow entry state
        entry_state = flow['states'][st.session_state.current_state]
        if 'message' in entry_state:
            message = get_message_text(entry_state['message'])
            
            # Build the full prompt including question if present
            full_message = message
            if 'question' in entry_state:
                question = entry_state['question']
                if question in st.session_state.nav_params['messages']:
                    question = get_message_text(question)
                full_message = f"{message}\n\n{question}"
            
            # Generate AI response with the message context
            system_prompt = f"You are a professional healthcare assistant. Present this information naturally: {full_message}"
            response = generate_ai_response(system_prompt)
            
            if response:
                st.session_state.messages.append({"role": "assistant", "content": response})
        
        save_session()


def process_state_transition(selected_key=None, user_input=None):
    """Process state transition based on current state"""
    if not st.session_state.current_flow or not st.session_state.current_state:
        return
    
    flows = st.session_state.nav_params.get('flows', {})
    flow = flows[st.session_state.current_flow]
    current_state = flow['states'][st.session_state.current_state]
    
    # Handle user selection
    if selected_key:
        st.session_state.stat_data['collected_data']['last_choice'] = selected_key
    
    # Determine next state
    next_state = None
    
    if 'next_router' in current_state:
        # Use router to determine next state
        router_key = current_state['next_router']
        next_state = evaluate_router(router_key, st.session_state.stat_data['collected_data'])
    elif 'next' in current_state:
        # Direct next state
        next_state = current_state['next']
    
    if next_state and next_state in flow['states']:
        st.session_state.current_state = next_state
        next_state_data = flow['states'][next_state]
        
        # Generate message for next state
        if 'message' in next_state_data or 'question' in next_state_data:
            # Build the content from message and/or question
            content_parts = []
            
            if 'message' in next_state_data:
                message = get_message_text(next_state_data['message'])
                content_parts.append(message)
            
            if 'question' in next_state_data:
                question = next_state_data['question']
                if question in st.session_state.nav_params['messages']:
                    question = get_message_text(question)
                content_parts.append(question)
            
            full_content = "\n\n".join(content_parts)
            
            # Generate AI response with context
            lang_name = "Hungarian" if st.session_state.language == "hungarian" else "English"
            system_prompt = f"You are a professional healthcare assistant specializing in cervical cancer prevention and HPV information. Present this information naturally and conversationally in {lang_name}: {full_content}"
            response = generate_ai_response(system_prompt)
            
            if response:
                st.session_state.messages.append({"role": "assistant", "content": response})
        elif next_state_data.get('type') == 'info':
            # For info states without explicit message, try to get the message anyway
            if 'message' in next_state_data:
                message = get_message_text(next_state_data['message'])
                lang_name = "Hungarian" if st.session_state.language == "hungarian" else "English"
                system_prompt = f"You are a professional healthcare assistant. Present this information naturally in {lang_name}: {message}"
                response = generate_ai_response(system_prompt)
                
                if response:
                    st.session_state.messages.append({"role": "assistant", "content": response})
        
        save_session()


# Main UI
if not st.session_state.started:
    st.markdown("<h1 style='color: #5e17eb; text-align: center'>Welcome to ScreenGPT 2.0 👨🏽‍⚕️<br>Please select language!</h1>", unsafe_allow_html=True)
    col0, col1, col2, col3 = st.columns([0.3, 0.2, 0.2, 0.3])
    col1.button("English", on_click=load_lang, kwargs={"lang": "english"}, use_container_width=True)
    col2.button("Hungarian", on_click=load_lang, kwargs={"lang": "hungarian"}, use_container_width=True)
    
    st.markdown("<h3 style='color: #5e17eb; text-align: center'>or<br>If you want to resume a previous session, you can enter the ID here.</h3>", unsafe_allow_html=True)
    session_input = st.text_input('ID', label_visibility="hidden")
    
    if session_input:
        if load_session(session_input):
            st.rerun()

if st.session_state.started:
    # Initialize messages
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": st.session_state.texts.get('greeting', 'Hello!')}
        ]
    
    # Display chat history
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            st.chat_message(msg["role"]).write(msg["content"])
    
    # Initialize flow if not set
    if len(st.session_state.messages) == 1:
        # Auto-select cervical flow
        select_flow('cervical')
        st.rerun()
    
    # Show session ID in sidebar
    if st.session_state.sessionID:
        with st.sidebar:
            st.write(st.session_state.texts.get('write_ID', 'Your session ID is:'))
            st.code(st.session_state.sessionID)
            st.markdown(f"<p style='text-align: justify'>{st.session_state.texts.get('ID_description', '')}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: justify'>{st.session_state.texts.get('feedback', '')}</p>", unsafe_allow_html=True)
            st.link_button(
                st.session_state.texts.get('feedback_label', 'Feedback'),
                st.session_state.texts.get('feedback_url', '#')
            )
    
    # Handle current state
    if st.session_state.current_flow and st.session_state.current_state:
        flows = st.session_state.nav_params.get('flows', {})
        flow = flows.get(st.session_state.current_flow, {})
        states = flow.get('states', {})
        current_state_data = states.get(st.session_state.current_state, {})
        
        state_type = current_state_data.get('type')
        
        if state_type == 'input' and st.session_state.current_state == 'gender_age':
            # Gender and age input form
            with st.form("gender_age_form"):
                col1, col2 = st.columns(2)
                gender = col1.selectbox(
                    st.session_state.texts.get("gender", "Gender"),
                    st.session_state.texts.get("gender_options", ["Female", "Male"])
                )
                age = col2.number_input(
                    label=st.session_state.texts.get('age', 'Age'),
                    min_value=18,
                    max_value=100,
                    step=1
                )
                submit = st.form_submit_button("OK", use_container_width=True)
                
                if submit:
                    # Store collected data
                    st.session_state.stat_data['collected_data']['age'] = age
                    if gender in ["Férfi", "Male"]:
                        st.session_state.stat_data['collected_data']['gender'] = "male"
                    else:
                        st.session_state.stat_data['collected_data']['gender'] = "female"
                    
                    # Add user message in the selected language
                    if st.session_state.language == "hungarian":
                        gender_text = "férfi" if gender in ["Férfi", "Male"] else "nő"
                        user_msg = f"{age} éves {gender_text} vagyok."
                    else:
                        gender_text = "male" if gender in ["Férfi", "Male"] else "female"
                        user_msg = f"I am a {age} years old {gender_text}."
                    
                    st.session_state.messages.append({
                        "role": "user",
                        "content": user_msg
                    })
                    
                    # For input states, manually process the next_router
                    if 'next_router' in current_state_data:
                        router_key = current_state_data['next_router']
                        next_state = evaluate_router(router_key, st.session_state.stat_data['collected_data'])
                        
                        if next_state and next_state in flow['states']:
                            st.session_state.current_state = next_state
                            next_state_data = flow['states'][next_state]
                            
                            # Generate message for next state
                            if 'message' in next_state_data or 'question' in next_state_data:
                                content_parts = []
                                
                                if 'message' in next_state_data:
                                    message = get_message_text(next_state_data['message'])
                                    content_parts.append(message)
                                
                                if 'question' in next_state_data:
                                    question = next_state_data['question']
                                    if question in st.session_state.nav_params['messages']:
                                        question = get_message_text(question)
                                    content_parts.append(question)
                                
                                full_content = "\n\n".join(content_parts)
                                
                                # Generate AI response with context
                                lang_name = "Hungarian" if st.session_state.language == "hungarian" else "English"
                                system_prompt = f"You are a professional healthcare assistant specializing in cervical cancer prevention and HPV information. Present this information naturally and conversationally in {lang_name}: {full_content}"
                                response = generate_ai_response(system_prompt)
                                
                                if response:
                                    st.session_state.messages.append({"role": "assistant", "content": response})
                            
                            save_session()
                    
                    st.rerun()
        
        elif state_type == 'question' and 'options' in current_state_data:
            # Display option buttons
            option_set_key = current_state_data['options']
            option_set = get_option_set(option_set_key)
            
            for i, (key, label) in enumerate(zip(option_set['keys'], option_set['labels'])):
                if st.button(label, key=f"btn_{key}_{i}", use_container_width=True):
                    # Add user message
                    st.session_state.messages.append({
                        "role": "user",
                        "content": label
                    })
                    
                    # Process transition with selected option
                    process_state_transition(selected_key=key)
                    st.rerun()
        
        elif state_type == 'final' or state_type == 'info':
            # Free conversation mode
            if prompt := st.chat_input():
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.chat_message("user").write(prompt)
                
                lang_name = "Hungarian" if st.session_state.language == "hungarian" else "English"
                system_prompt = f"You are a professional healthcare assistant specializing in cervical cancer prevention and HPV information. Provide accurate, helpful information in {lang_name}. Always respond in {lang_name} language."
                response = generate_ai_response(system_prompt)
                
                if response:
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.chat_message("assistant").write(response)
                    save_session()
                    st.rerun()
