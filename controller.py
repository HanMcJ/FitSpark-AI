# Controller.py
import streamlit as st
from datetime import datetime
import numpy as np
from PIL import Image
import pickle


# EVENT LOGGING FUNCTION ----------------
def log_event(event_type, event_data=None, task=None):
    log_entry = {
        "user_id": st.session_state.user_id,
        "timestamp": datetime.now().isoformat(),  # Store timestamp in ISO format
        "page": st.session_state.page, # Current page the user is on 
        "Task": task, # Current task the user is working on
        "workout_id": st.session_state.selected_workout if st.session_state.selected_workout else None, # ID of the selected workout
        "category": st.session_state.selected_category if st.session_state.selected_category else None, # Selected category
        "event_type": event_type, # Type of event (view, click, like, dislike)
        "event_data": event_data   # Additional data related to the event
    }
    st.session_state.logs.append(log_entry)


# Function to load images
@st.cache_data
def load_image(path):
    img = Image.open(path)
    img.thumbnail((300, 200), resample=Image.LANCZOS)  # Resize image to fit the card
    return img 



# Function to identify which task is active 
def get_active_task():
    if st.session_state.task2_active:
        return "Task 2"
    elif st.session_state.task4_active:
        return "Task 4"
    else:
        return None
    


# Function to load the q-table 
def load_q_table(path):
    if "q_table" not in st.session_state:
        with open(path, "rb") as f: 
            q_table_data = pickle.load(f)
        st.session_state.q_table = q_table_data["q_table"]
    return st.session_state.q_table


# Function to update the Q-table when user gives feedback 
def update_q_table(state, action, reward, next_state, alpha=0.1, gamma=0.9):
     q = st.session_state.q_table
     old_value = q[state, action]
     next_max = np.max(q[next_state])
     new_value = old_value + alpha * (reward + gamma * next_max - old_value)
     q[state, action] = new_value
     st.session_state.q_table = q 

