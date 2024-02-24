import os
import base64
import time
import pytz
import pprint
import json
import streamlit as st
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# APIキーの設定
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
)

st.set_page_config(
    page_title="Stream Chat",
    page_icon="👁‍🗨",
#    initial_sidebar_state="collapsed",
    layout="wide",
)
#st.title("Stream Chat")

hide_streamlit_style = """
<style>
    #MainMenu {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    [data-testid="stSidebarNav"] {visibility: hidden;}
    [data-testid="stSidebarNav"] [data-testid="stSidebarNavItems"] {max-height: 0;}
    [data-testid="stSidebarNav"] [data-testid="stSidebarNavItems"] li  {display: none;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
st.sidebar.page_link("app.py", label="home", icon="🏠")
st.sidebar.page_link("pages/chat.py", label="Stream Chat", icon="👁‍🗨")
st.sidebar.page_link("pages/roomb.py", label="ROOM B", icon="🧊")
st.sidebar.page_link("pages/roomx.py", label="ROOM X", icon="💖")


game_status = {
    "now_gas": "A",
    "chat_count": 0,
    "status": "init",
    "sex_status": "init",
    "is_clear": "",
    "clear_result": "",
    "used_functions": [],
    "game_messages": [],
    "alive_peoples": {
        "A": 1,
        "B": 1,
    }
}

if "game_status" not in st.session_state:
    st.session_state.game_status = game_status

def get_now_time(timezone_str='Asia/Tokyo'):
    try:
        timezone = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        timezone = pytz.timezone('Asia/Tokyo')

    current_time = datetime.now(timezone)
    return current_time.strftime('%Y-%m-%d %H:%M:%S %Z')

functions_dict = {
    'get_now_time': get_now_time,
}

my_functions = [
    {
        "name": "get_now_time",
        "description": "現在の時間を取得して返す",
        "parameters": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "タイムゾーン"
                },
            },
            "required": ["timezone"]
        }
    }
]

def openai_chat_completion_create(back_messages):
    response = client.chat.completions.create(
        model = "gpt-4-0125-preview", # gpt-4-0125-preview or gpt-4-1106-preview gpt-3.5-turbo-1106
        messages = back_messages,
        functions = my_functions,
        function_call = "auto",
        stream = True,
    )
    return response

def run_conversation(back_messages, front_assistant_msgs):
    game_status = st.session_state.game_status
    response = openai_chat_completion_create(back_messages)

    function_name = ""
    function_arguments = ""
    assistant_msg = ""

    for chunk in response:
        if chunk.choices[0].delta.function_call:
            if chunk.choices[0].delta.function_call.arguments == "" and chunk.choices[0].delta.function_call.name:
                function_name = chunk.choices[0].delta.function_call.name

            if chunk.choices[0].delta.function_call.arguments and chunk.choices[0].delta.function_call.name == None:
                function_arguments += chunk.choices[0].delta.function_call.arguments

        if chunk.choices[0].finish_reason is not None:
            if chunk.choices[0].finish_reason == "function_call":

                back_messages.append({
                    "role": "assistant",
                    "content": "",
                    "function_call": {
                        "name": function_name,
                        "arguments": function_arguments
                    }
                })

                if function_name and function_arguments:
                    function_arguments = json.loads(function_arguments)

                if function_name in functions_dict:
                    arg = ""
                    if function_name == "get_now_time":
                        arg = function_arguments.get("timezone")
                        functions_return = functions_dict[function_name](arg)

                    colored_text = "<div style='color: #10965e; text-align: center; padding: 1px; background: #f1f1f1; border-radius: 10px; max-width: 80%; margin: 0 auto 10px;'>" + "「" + function_name + "(" + arg + ")」実行</div>"

                    for game_message in st.session_state.game_status["game_messages"]:
                        colored_text += "<div style='color: #10965e; padding: 1px; margin-bottom: 10px;'>" + game_message + "</div>"

                    game_status["game_messages"] = []
                    front_assistant_msgs.append({
                        "type": "markdown",
                        "content": colored_text
                    })
                    st.markdown(colored_text, unsafe_allow_html=True)

                    back_messages.append({
                        "role": "function",
                        "name": function_name,
                        "content": functions_return,
                    })

                    run_conversation(back_messages, front_assistant_msgs)

        if chunk.choices[0].delta.content and assistant_msg == "":
            assistant_response_area = st.empty()

        if chunk.choices[0].delta.content:
            assistant_msg += chunk.choices[0].delta.content
            assistant_response_area.write(assistant_msg)

    if assistant_msg:
        back_messages.append({
            "role": "assistant",
            "content": assistant_msg
        })
        front_assistant_msgs.append({
            "type": "text",
            "content": assistant_msg
        })
        st.session_state.front_messages.append({
            "role": "assistant",
            "content": front_assistant_msgs
        })

if "back_messages" not in st.session_state:
    st.session_state.back_messages = [{
        "role": "system",
        "content": """
日本語で会話してください。
        """
    }]

if "front_messages" not in st.session_state:
    st.session_state.front_messages = []

#with st.chat_message("❗"):
#    st.markdown("初期メッセージ", unsafe_allow_html=True)

user_msg = st.chat_input("ここにメッセージを入力")
if user_msg:

    game_status = st.session_state.game_status
    game_status["game_messages"] = []

    # ユーザの入力をチャット履歴に追加する
    st.session_state.back_messages.append({"role": "user", "content": user_msg})
    st.session_state.front_messages.append({"role": "user", "content": user_msg})

    # これまでのチャット履歴を全て表示する
    for message in st.session_state.front_messages:
        if message["content"] and message["role"] != "function":
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])

                if message["role"] == "assistant":
                    for content in message["content"]:
                        if content["type"] == "text":
                            assistant_response_area = st.empty()
                            assistant_response_area.write(content["content"])

                        if content["type"] == "markdown":
                            st.markdown(content["content"], unsafe_allow_html=True)

    front_assistant_msgs = []
    with st.chat_message("assistant"):
        run_conversation(st.session_state.back_messages, front_assistant_msgs)

