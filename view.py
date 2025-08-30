import streamlit as st
from model_sub_workout_data import sub_workouts, sub_workout_lookup  # Import sub_workouts and sub_workout_lookup from the model
import random
import pickle # for Q-learning agent
import numpy as np
import os # for images
from PIL import Image # for image handling
import pandas as pd # for data manipulation
from datetime import datetime, timedelta  # for user research
from controller import log_event, get_active_task, load_q_table, update_q_table, load_image  
import sys
import os 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# CONFIG ------------------
st.set_page_config(page_title="FitSpark", layout="wide")


# Display toast message if present
if "toast_message" in st.session_state:
    msg, icon = st.session_state.toast_message
    st.toast(msg, icon=icon)
    del st.session_state.toast_message  # Clear the message after displaying it



# User ID setup ----------------
# List of User IDs
valid_user_ids = ["user1", "user2", "user3", "user4", "user5"]  # Example user IDs for testing

# User ID input & validation 
if "user_id" not in st.session_state:
    st.session_state.user_id = ""  # Initialize user ID as an empty string

if "user_validated" not in st.session_state:
    st.session_state.user_validated = False  # Track if user ID has been validated

# Show input field if user ID is not validated
if not st.session_state.user_validated:
    user_input = st.text_input("Enter your user ID", value="", key="user_id_input")
    # Validate user ID
    if user_input:
        if user_input in valid_user_ids:
            st.session_state.user_id = user_input
            st.session_state.user_validated = True
            st.success(f"User ID '{user_input}' validated successfully!")
            st.rerun()  # Refresh the page to apply changes
        else:
            st.error("Invalid user ID. Please enter a valid user ID to continue.")
    st.stop()
else:
    # Display the validated user ID
    st.sidebar.write(f"Logged in as: {st.session_state.user_id}")


# Download CSV file 
if st.session_state.get("logs"):
    logs_df = pd.DataFrame(st.session_state.logs)
    csv_data = logs_df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="Download Logs as CSV",
        data=csv_data,
        file_name=f"{st.session_state.user_id}_logs.csv",
        mime="text/csv"
    )


# SESSION STATE SETUP ---------------
if "selected_category" not in st.session_state:
    st.session_state.selected_category = None
if "selected_workout" not in st.session_state:
    st.session_state.selected_workout = None
if "saved_workouts" not in st.session_state:
    st.session_state.saved_workouts = []
if "liked_workouts" not in st.session_state:
    st.session_state.liked_workouts = []
if "disliked_workouts" not in st.session_state:
    st.session_state.disliked_workouts = []
if "selected_sub_workout" not in st.session_state:
    st.session_state.selected_sub_workout = None # This is for the sub workout details piece
if "recommendation_offset" not in st.session_state:
    st.session_state.recommendation_offset = 0





# INITIALIZE USER LOGGING ----------------
# Store all log events in a list
if "logs" not in st.session_state:
    st.session_state.logs = []

# USER/ SESSION ID ENTRY ---------------
if "user_id" not in st.session_state:
    st.session_state.user_id = "" # Initialize user ID as an empty string
# If the user ID is not set, prompt for it
if not st.session_state.user_id:
    st.session_state.user_id = st.text_input("Enter your user ID", value="", key="user_id_input")

# Stop the app if no user ID is provided
if not st.session_state.user_id:
    st.error("Please enter a valid user ID to continue.")
    st.stop()  # Stop further execution if no user ID is provided




# TASK STATE ----------------
# Initialize task state to track the current task

# Task 2
if "task2_active" not in st.session_state:
    st.session_state.task2_active = False  # Task 2 is not active by default
if "task2_start_time" not in st.session_state:
    st.session_state.task2_start_time = None  
if "task2_end_time" not in st.session_state:
    st.session_state.task2_end_time = None  

# Task 4
if "task4_active" not in st.session_state:
    st.session_state.task4_active = False  # Task 4 is not active by default
if "task4_start_time" not in st.session_state:
    st.session_state.task4_start_time = None  
if "task4_end_time" not in st.session_state:
    st.session_state.task4_end_time = None  



# Load the Q-table from the specified path
#Q_TABLE_PATH = os.path.join("Adaptation_Engine", "RL_Algorithms", "q_table_V1.pickle") # version for deployment
Q_TABLE_PATH = os.path.join("FitSpark-AI","Adaptation_Engine", "RL_Algorithms", "q_table_V1.pickle") # version for local testing
q_values = load_q_table(Q_TABLE_PATH)
state = 0



# sidebar navigation ---------------
st.sidebar.title("Navigation")


# Function to display a workout card with details and buttons
# Display workout card function 
def display_workout_card(
    sub, # workout dict
    key_prefix="", # for unique keys
    
):
    
    image_name = sub.get("image_filename", "placeholder.jpg")
    img_path = os.path.join(BASE_DIR, "images", image_name) # Use BASE_DIR to construct the path                

    if os.path.exists(img_path):
        st.image(load_image(img_path), use_container_width=True)

    else:
        st.warning(f"Image not found: {img_path}")



    st.markdown(
        f"""
        <div style='background-color:#618685; padding:15px; border-radius:10px; margin-bottom:10px; min-height:220px; display:flex; flex-direction:column; justify-content:space-between; margin-left:auto; margin-right:auto;'>
            <div>
            <strong>{sub['name']}</strong><br>
            <em>Category:</em> {sub.get('category', 'N/A')}<br>
            <em>Duration:</em> {sub['duration']}<br>
            <em>Difficulty:</em> {sub['difficulty']}<br>
            <p>{sub['description']}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

 
    # Save, Like, Dislike buttons 
    btn1, btn2, btn3 = st.columns(3)
    active_task = get_active_task() # Get the active task
    if "id" in sub:
        # Save button
        if btn1.button("Add to My Workouts", key=f"{key_prefix}save_{sub['id']}"):
            if sub["id"] not in st.session_state.saved_workouts:
                st.session_state.saved_workouts.append(sub["id"])
                st.success(f"Added **{sub['name']}** to My Workouts!")
                # Log the event
                log_event(
                    event_type="add_to_my_workouts",
                    event_data={"workout_id": sub["id"], "workout_name": sub["name"]},
                    task=active_task,  # Log the active task    
                )

            else:
                st.warning(f"**{sub['name']}** is already in your saved workouts.")
    else:
        st.warning(f"Workout '{sub.get('name', 'Unnamed')}' is missing an ID and cannot be added.")




    # Like button 
    if btn2.button("👍 Like", key=f"{key_prefix}_like_{sub['name']}"):
        st.session_state.liked_workouts.append(sub)

        # Debug statement
        #st.write("Q-table before update:", st.session_state.q_table)

        
        # Q-learning update positive reward: 
        state = 0
        action = sub["id"]
        reward = 3 # *
        next_state = 0
        update_q_table(state, action, reward, next_state)

        # Log the event
        log_event(
            event_type="like",
            event_data={"workout_id": sub["id"], "workout_name": sub["name"]},
            task=active_task,  # Log the active task
        )


        # Give a small reward to other workouts in the same category
        for w in sub_workout_lookup.values():
            if w.get("category") == sub.get("category") and w["id"] != sub["id"]:
                update_q_table(state, w["id"], 1, next_state) 

        # Debug statement
        #st.write("Q-table after update:", st.session_state.q_table)
        
        # Refresh the recommendations
        st.session_state.reshuffle = True  # Set a flag to reshuffle the recommendations

        # store message for next rerun
        st.session_state.toast_message = (
            f"You liked **{sub['name']}**! ", "👍"  # Use a tuple to store both message and icon
        )
        st.rerun()

        
    # Dislike button
    # If the user dislikes a workout, update the Q-table with a negative reward
    if btn3.button("👎 Dislike", key=f"{key_prefix}_dislike_{sub['name']}"):
        st.session_state.disliked_workouts.append(sub)
        # Q-learning update negative reward:
        state = 0
        action = sub["id"]
        reward = -1
        next_state = 0
        update_q_table(state, action, reward, next_state)
        # Log the event
        log_event(
            event_type="dislike",
            event_data={"workout_id": sub["id"], "workout_name": sub["name"]},
            task=active_task,  # Log the active task
        )
        


        # Refresh the recommendations
        st.session_state.reshuffle = True  # Set a flag to reshuffle the recommendations


        st.session_state.toast_message = (
            f"You disliked **{sub['name']}**", "👎"  # Use a tuple to store both message and icon
        )
        st.rerun()


    # More details button
    if st.button("More details", key=f"{key_prefix}_details_{sub['name']}"):
        st.session_state.selected_sub_workout = sub
        st.rerun()


# Function to display sub-workout details in a card format
# This function is called when the user clicks on "More details" button
def display_workout_grid(workouts, key_prefix="", columns=3):
    for i in range(0, len(workouts), columns):
        row = st.columns(columns)
        for j in range(columns):
            if i + j < len(workouts):
                sub = workouts[i + j]
                with row[j]:
                    display_workout_card(sub, key_prefix=f"{key_prefix}_{i + j}")



# Function to display sub-workout full details with a back button 
def show_sub_workout_details(sub_workout):

    # display workout card with full details
    display_workout_card(sub_workout, key_prefix="details_")

    st.markdown("---")  # Add a horizontal line for separation

    # Display additional details
    if "steps" in sub_workout:
        st.subheader("Workout Steps")
        for step in sub_workout["steps"]:
            st.markdown(f"- {step}")

    if "benefits" in sub_workout: 
        st.subheader("Main Benefits")
        st.write(sub_workout["benefits"])



    if st.button(" Back"):
        st.session_state.selected_sub_workout = None
        st.rerun()
    st.write("Click 'Back' to return to the workout list.")
    st.markdown("---") # Add a horizontal line for separation


# SESSION STATE DEFAULTS -------
# Maintain page state
if "page" not in st.session_state:
    st.session_state.page = "Home"


# SIDEBAR NAVIGATION ------------
# Sidebar navigation updates state
st.sidebar.title("Select a Page")
selected = st.sidebar.radio("Go to", ["Home", "Exercise Workouts", "My workouts"])
if selected != st.session_state.page:

    st.session_state.selected_sub_workout = None # Always clear selection 


    if st.session_state.page == "Exercise Workouts": # Clear selection once leaving this page 
        st.session_state.selected_workout = None
        st.session_state.selected_category = None

    st.session_state.page = selected
    st.rerun()


# FUNCTION DEFINTIONS 
# HOME PAGE ---------------

def home_page():
    st.title("Welcome to FitSpark!")
    st.subheader("Train hard, train smart")
    with st.container():
            st.write("View your personalized workout recommendations")

    if st.session_state.selected_sub_workout: 
        show_sub_workout_details(st.session_state.selected_sub_workout)
        st.stop()


   # Task 2 Controls ---------------

    st.markdown("---")  # Add a horizontal line for separation

    # TASK 2 CONTROLS ---------------
    if not st.session_state.task2_active and not st.session_state.task2_end_time:
        if st.button("Start Task 2"):
            st.session_state.task2_active = True
            st.session_state.task2_start_time = datetime.now()
            st.session_state.task2_expiry_time = st.session_state.task2_start_time + timedelta(minutes=8)  # Task 2 expires in 8 minutes
            log_event("task_started", task="Task 2")
            st.rerun()

    # TASK 2 ACTIVE CONTROLS ---------------
    if st.session_state.task2_active:
        st.info("Task 2 is in progress. You have a maximum of 8 minutes to complete it. You can stop any time by clicking the button below.")

        # Show the time remaining for Task 2
        seconds_remaining = int((st.session_state.task2_expiry_time - datetime.now()).total_seconds())
        if seconds_remaining > 0:
            minutes, seconds = divmod(seconds_remaining, 60)
            st.write(f"Time remaining for Task 2: {minutes} minutes and {seconds} seconds")
        else: 
            # Auto-end when time is up 
            st.session_state.task2_active = False 
            st.session_state.task2_end_time = datetime.now()
            log_event(
                "task2_end", 
                {"duration__seconds": (st.session_state.task2_end_time - st.session_state.task2_start_time).total_seconds(), "auto": True},
                task="task2",

            )
            st.success("Task 2 has now ended.")
            st.rerun()  # Refresh the page to show the end message

            # Manual stop button
        if st.button("Stop Task 2"):
            st.session_state.task2_active = False
            st.session_state.task2_end_time = datetime.now()
            log_event(
                "task2_end", 
                {"duration__seconds": (st.session_state.task2_end_time - st.session_state.task2_start_time).total_seconds(), "auto": False},
                task="task2",
            )
            st.success("Task 2 has been stopped.")
            st.rerun()  # Refresh the page to show the end message

    # Message for when task 2 has ended
    if st.session_state.task2_end_time and not st.session_state.task2_active:
        st.success("Task 2 has ended. You can now proceed to task 3. Please refer to the test instructions for more details.")
        

    st.markdown("---")  # Add a horizontal line for separation



    # TASK 4 CONTROLS ---------------
    # Task 4 controls
    if not st.session_state.task4_active and not st.session_state.task4_end_time:
        if st.button("Start Task 4"):
            st.session_state.task4_active = True
            st.session_state.task4_start_time = datetime.now()
            st.session_state.task4_expiry_time = st.session_state.task4_start_time + timedelta(minutes=8)  # Task 4 expires in 8 minutes
            log_event("task_started", task="Task 4")

    # TASK 4 ACTIVE CONTROLS ---------------
    if st.session_state.task4_active: 
        st.info("Task 4 is in progress. You have a maximum of 8 minutes to complete it. You can stop any time by clicking the button below.")

        # Show the time remaining for Task 4
        seconds_remaining = int((st.session_state.task4_expiry_time - datetime.now()).total_seconds())
        if seconds_remaining > 0:
            minutes, seconds = divmod(seconds_remaining, 60)
            st.write(f"Time remaining for Task 4: {minutes} minutes and {seconds} seconds")
        else: 
            # Auto-end when time is up 
            st.session_state.task4_active = False 
            st.session_state.task4_end_time = datetime.now()
            log_event(
                "task4_end", 
                {"duration__seconds": (st.session_state.task4_end_time - st.session_state.task4_start_time).total_seconds(), "auto": True},
                task="task4",
            )
            st.success("Task 4 has now ended.")

        # Manual stop button
        if st.button("Stop Task 4"):
            st.session_state.task4_active = False
            st.session_state.task4_end_time = datetime.now()
            log_event(
                "task4_end", 
                {"duration__seconds": (st.session_state.task4_end_time - st.session_state.task4_start_time).total_seconds(), "auto": False},
                task="task4",
            )
            st.success("Task 4 has been stopped.")

    # Message for when task 4 has ended
    if st.session_state.task4_end_time and not st.session_state.task4_active:
        st.success("Task 4 has ended. You can now proceed to task 5. Please refer to the test instructions for more details.")

    st.markdown("---")  # Add a horizontal line for separation


    # Display the top 3 recommended workouts based on the Q-table
    # adding to track live feedback  impact 
    state = 0
    top_indices = np.argsort(st.session_state.q_table[state])[::-1][:3]
    
    # Display the top 3 recommended workouts as cards ***
    st.markdown("### Top 3 Recommended Workouts")
    top_workouts = [sub_workout_lookup.get(idx) for idx in top_indices if idx in sub_workout_lookup]    
    if top_workouts:
        cols = st.columns(3)
        for i, workout in enumerate(top_workouts):
            with cols[i % 3]:
                display_workout_card(workout, key_prefix=f"top_{i}")
    else:
        st.info("No recommended workouts available right now.")
    st.markdown("---")

   

    st.header("Browse Workouts")



        # Clear button logic 
    if "clear_search" not in st.session_state:
        st.session_state.clear_search = False 
        
    if st.session_state.clear_search:
        default_search = ""
        st.session_state.clear_search = False 
    else:
        default_search = st.session_state.get("search_box", "")

    # Search bar
    search_query = st.text_input("Search for workouts by keywords such as Pilates, Strength or Running", value=default_search, key="search_box").strip()



    # Adding clear button 
    if search_query or st.session_state.get("saved_search_query"):
        if st.button("Clear Search"):
            st.session_state.clear_search = True
            st.session_state.filtered_search_results = []  # Clear the filtered search results
            st.session_state.saved_search_query = ""  # Clear the saved search query
            st.rerun()


    # Heading 
    if search_query:
        st.subheader(f"showing results for: '{search_query.strip()}'") # show current search query

    elif st.session_state.get("filtered_search_results") and st.session_state.get("saved_search_query"):
        st.subheader(f"Showing results for: '{st.session_state.saved_search_query}'")

    else:
        st.subheader("Some More Workouts You Might Like")


        if "sampled_subs" not in st.session_state or st.session_state.get("reshuffle", False):

            
            # updated logic for filtering out disliked workouts
            all_ids = list(sub_workout_lookup.keys())
            disliked_ids = {w["id"] for w in st.session_state.disliked_workouts}
            liked_ids = {w["id"] for w in st.session_state.liked_workouts}

            # only recommend workouts that are not disliked
            filtered_ids = [i for i in all_ids if i not in disliked_ids]

            # sort by Q-value
            q_values_sorted = sorted(filtered_ids, key=lambda i: st.session_state.q_table[state, i], reverse=True)

            # Push liked workouts to the front of the list
            q_values_sorted = sorted(q_values_sorted, key=lambda i: (i not in liked_ids, -st.session_state.q_table[state, i]))


            # If the user clicked "Show more", increment the offset
            if st.session_state.get("reshuffle", False):
                st.session_state.recommendation_offset += 6 

            # Check if the offset is past the end of the list; if so, loop back to the start
            if st.session_state.recommendation_offset >= len(q_values_sorted):
                st.session_state.recommendation_offset = 0
                st.info("You've seen all our recommendations! Here they are again from the top.")

            # Get the next slice of workout IDs based on the offset
            start_index = st.session_state.recommendation_offset
            end_index = start_index + 6 # Show 6 workouts
            recommended_ids_slice = q_values_sorted[start_index:end_index]
            
            # Fetch the workout details from the lookup dictionary
            st.session_state.sampled_subs = [sub_workout_lookup[i] for i in recommended_ids_slice if i in sub_workout_lookup]
                
            # Reset the reshuffle flag
            st.session_state.reshuffle = False

        filtered_subs = st.session_state.sampled_subs






    all_subs = [w for sublist in sub_workouts.values() for w in sublist]

    if search_query:
        filtered_subs = [
            w for w in all_subs
            if search_query.lower() in w["name"].lower()
            or search_query.lower() in w["description"].lower()
            or search_query.lower() in w.get("difficulty", "").lower()
        ]


        # Sort filtered results by Q-value (highest first)
        state = 0
        filtered_subs.sort(key=lambda w: st.session_state.q_table[state, w["id"]], reverse=True)  # Sort by Q-value
        st.session_state.filtered_search_results = filtered_subs  # Store the filtered results in session state for later use
        st.session_state.saved_search_query = search_query  # Save the search query


        # display the filtered search results in a grid 
        display_workout_grid(filtered_subs, key_prefix="home", columns=3) # Display the workout cards in a grid format


    elif st.session_state.get("filtered_search_results"):
        display_workout_grid(st.session_state.filtered_search_results, key_prefix="home", columns=3) # Display the workout cards in a grid format
    
    else: 
        if "sampled_subs" not in st.session_state:
            st.session_state.sampled_subs = []

        filtered_subs = st.session_state.sampled_subs
        display_workout_grid(filtered_subs, key_prefix="home", columns=3) # Display the workout cards in a grid format

    
    # Refresh sample workouts
    if st.button("Show more workouts"):
        active_task = get_active_task()  # Get the active task
        log_event(
            event_type="show_more_workouts",
            event_data={"current_offset": st.session_state.recommendation_offset},
            task=active_task,  # Log the active task
        )
        st.session_state.reshuffle = True
        st.rerun()




# WORKOUTS PAGE ---------


def exercise_workouts_page():
    st.title("Exercise Workouts")
            

    workouts = {
        "Strength Workouts": ["Weight-based", "Calisthenics", "Low-impact"],
        "Mind-body Workouts": ["Yoga", "Pilates", "Barre"],
        "Conditioning Workouts": ["Mobility", "Flexibility", "Core"],
        "Running": ["Road Running", "Treadmill Running", "Track Running"],
        "Gym Cardio": ["Stair Climb", "Elliptical", "Rowing"],
        "Other Cardio": ["Cycling", "Skipping", "Swimming"],
        "Hybrid workouts": ["Circuit", "CrossFit", "HIIT"],
    }
    placeholder_url = "https://via.placeholder.com/150"

    images = {
        "Weight-based": "https://images.pexels.com/photos/949126/pexels-photo-949126.jpeg",
        "Low-impact": "https://images.pexels.com/photos/8846567/pexels-photo-8846567.jpeg",
        "Calisthenics": "https://images.pexels.com/photos/4775197/pexels-photo-4775197.jpeg",
        "Yoga": "https://images.pexels.com/photos/5038900/pexels-photo-5038900.jpeg",
        "Pilates": "https://images.pexels.com/photos/4534632/pexels-photo-4534632.jpeg",
        "Barre": "https://images.pexels.com/photos/10628969/pexels-photo-10628969.jpeg",
        "Mobility": "https://images.pexels.com/photos/6339398/pexels-photo-6339398.jpeg",
        "Flexibility": "https://images.pexels.com/photos/4775227/pexels-photo-4775227.jpeg",
        "Core": "https://images.pexels.com/photos/6516225/pexels-photo-6516225.jpeg",
        "Road Running": "https://images.pexels.com/photos/5319375/pexels-photo-5319375.jpeg",
        "Treadmill Running": "https://images.pexels.com/photos/1954524/pexels-photo-1954524.jpeg",
        "Track Running": "https://images.pexels.com/photos/3763869/pexels-photo-3763869.jpeg",
        "HIIT": "https://images.pexels.com/photos/4164658/pexels-photo-4164658.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
        "Cycling": "https://images.pexels.com/photos/13799203/pexels-photo-13799203.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
        "Swimming": "https://images.pexels.com/photos/1263349/pexels-photo-1263349.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
        "Elliptical": "https://images.pexels.com/photos/7031706/pexels-photo-7031706.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
        "Rowing": "https://images.pexels.com/photos/6551414/pexels-photo-6551414.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
        "Stair Climb": "https://images.pexels.com/photos/4422912/pexels-photo-4422912.jpeg", 
        "Skipping": "https://images.pexels.com/photos/6339693/pexels-photo-6339693.jpeg",
        "Circuit": "https://images.pexels.com/photos/4720537/pexels-photo-4720537.jpeg",
        "CrossFit": "https://images.pexels.com/photos/949130/pexels-photo-949130.jpeg", 
        

    }


    # Logic for dynamic list ordering based on Q-values: 
    # 1 - Calculate total score of each category based on the Q-values of its sub-workouts
    state = 0
    category_q_values = {main_cat: [] for main_cat in workouts.keys()}

    # Group the Q-values by category
    for sub_cat_name, sub_cat_workouts in sub_workouts.items():
        for main_cat_name, main_cat_sub_cats in workouts.items():
            if sub_cat_name in main_cat_sub_cats:
                for workout in sub_cat_workouts:
                    q_value = st.session_state.q_table[state, workout["id"]]
                    category_q_values[main_cat_name].append(q_value)
    # Calculate the average Q-value for each main category
    category_scores = {}
    for category, q_list in category_q_values.items():
        if q_list:
            category_scores[category] = np.mean(q_list)
        else:
            category_scores[category] = 0 # Default score when no workouts are in this category

    # 2 - Sort categories by their average Q-value score
    sorted_main_categories = sorted(category_scores, key=lambda k: category_scores[k], reverse=True) 


    # Show full sub-workout details if selected 
    if st.session_state.selected_sub_workout: 
            show_sub_workout_details(st.session_state.selected_sub_workout)
            st.stop()

    elif st.session_state.selected_workout:
            st.subheader(f"{st.session_state.selected_workout} Workouts")
            data = sub_workouts.get(st.session_state.selected_workout, [])
            if data:
                
                display_workout_grid(data, key_prefix="ex", columns=3) # Display the workout cards in a grid format
                st.write("Double click below to view other workouts in this category") # Help message        
                if st.button("Back to workout list"):
                    st.session_state.selected_workout = None

            else: 
                    
                st.write("No sub-workouts found.")

                if st.button("Back to workout list"):
                    st.session_state.selected_workout = None

    elif st.session_state.selected_category:
                st.header(st.session_state.selected_category)
                selected_workouts = workouts.get(st.session_state.selected_category, [])
                cols = st.columns(3)
                for i, workout in enumerate(selected_workouts):
                    with cols[i % 3]:
                        st.image(images.get(workout, placeholder_url), width=250)
                        if st.button(workout, key=f"{st.session_state.selected_category}_{workout}"):
                            st.session_state.selected_workout = workout
                            st.rerun()

                st.write("Double click below to view the full list of workout categories") # Help message

                if st.button("Back to categories"):
                    st.session_state.selected_category = None

    else:
                st.header("Browse Workout Categories")

                st.write("Select a category to view relevant workouts")

                #Debugging Aid - Check categories sorted by Q-value
                #st.write("sorted categories by Q-value:", sorted_main_categories)
                #st.write("category scores:", category_scores)

                for category in sorted_main_categories:
                    example_workouts = workouts.get(category, [])   
                    st.subheader(category)
                    cols = st.columns(3)
                    for i, workout in enumerate(example_workouts):
                        with cols[i % 3]:
                            st.image(images.get(workout, placeholder_url), width=250)
                            if st.button(workout, key=f"{category}_{workout}"):
                                
                                # Log the event of selecting a workout category
                                active_task = get_active_task()  # Get the active task
                                log_event(
                                    event_type="select_workout",
                                    event_data={"category": category, "workout": workout},
                                    task=active_task  # Log the active task
                                )

                                st.session_state.selected_category = category
                                st.session_state.selected_workout = workout
                                st.rerun() 

# MY WORKOUTS PAGE ----------

def my_workouts_page():     
    st.title("My Workouts")


    # Check if the user has selected a sub-workout to view details
    if st.session_state.selected_sub_workout: 
        show_sub_workout_details(st.session_state.selected_sub_workout)
        st.stop()


    if "workout_removed" in st.session_state: 
        st.success(st.session_state.workout_removed)
        del st.session_state.workout_removed

    if st.session_state.saved_workouts:
        saved_workouts_objs = [sub_workout_lookup.get(saved_id) for saved_id in st.session_state.saved_workouts if sub_workout_lookup.get(saved_id)] # Get the saved workouts objects from the lookup dict
        workout_to_remove = None

        for i in range(0, len(saved_workouts_objs), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(saved_workouts_objs):
                    workout = saved_workouts_objs[i + j]
                    with cols[j]:
                        display_workout_card(workout, key_prefix=f"my_{i + j}")
                        if st.button("Remove Workout", key=f"remove_{workout['id']}"):
                            workout_to_remove = workout["id"]


        # If the user clicked "Remove Workout", remove it from the saved workouts list
        if workout_to_remove is not None:
            st.session_state.saved_workouts. remove(workout_to_remove)
            st.session_state.workout_removed = "Workout successfully removed from your list"
            st.rerun() # Refresh page 

    else:
        st.info("You haven't added any workouts yet.")


     # Insert recommended workouts section on the My Workouts page
    state = 0
    num_recs = 9 # Number of recommended workouts to show

    # Exclude already saved workouts from recommendations
    all_workout_ids = set(sub_workout_lookup.keys())
    excluded_ids = set(st.session_state.saved_workouts)
    recs_candidate_ids = list(all_workout_ids - excluded_ids)
                              
    # Get the Q-values for the remaining workouts
    rec_q_values = [(wid, st.session_state.q_table[state, wid]) for wid in recs_candidate_ids]
    # Sort by Q-value (descending)
    rec_q_values_sorted = sorted(rec_q_values, key=lambda x: x[1], reverse=True)
    # Get the top recommended workouts
    top_rec_ids = [wid for wid, q in rec_q_values_sorted[:num_recs]]
    top_rec_workouts = [sub_workout_lookup[wid] for wid in top_rec_ids if wid in sub_workout_lookup]
                        
    if top_rec_workouts:
        st.markdown("### Recommended Workouts for You")
        
        display_workout_grid(top_rec_workouts, key_prefix="rec", columns=3) # Display the workout cards in a grid format
    



# Main page content logic
page = st.session_state.page

if page == "Home":
    home_page()
elif page == "Exercise Workouts":
    exercise_workouts_page()
elif page == "My workouts":
    my_workouts_page()
