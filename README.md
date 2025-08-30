# FitSpark-AI
####An AI-enhanced prototype fitness application built with Python V3.11 (and Streamlit) and developed as part of a Master's dissertation project. This version integrates a reinforcement learning (Q-learning) agent within the Adaptation Engine to personalize workout recommendations. The Q-learning agent is adapted from Gaspar-Figueiredo et al (2024): https://github.com/RESQUELAB/RL-UIAdaptation (full reference below). 

###Features 
- Personalized workout recommendations based on a pre-trained Q-agent. 
- Adaptive User Interface with dynamic content presentation, incorporating user feedback in real time. 
- Event logging for usability testing. 

###Repository Structure
***The application is inspired by the Model-View-Controller design pattern.***
***-Adaptation_Engine:***Contains the RL algorithm, training data, and Jupyter Notebooks used for training/testing the Q-learning agent. 
***-images:***Stores images for the UI. 
***controller.py:***Logic for event logging, image loading, Q-table management and Q-table updates. 
***model_sub_workout_data.py:***Contains the dataset of workouts and associated details. 
***view.py:***Streamlit frontend implementation of the application, including workout display and navigation. 

###Installation & Running
1. After cloning the repository, it is recommended to create and activate a virtual environment 
python -m venv venv
source ven/bin/activate # On Mac/Linux
venv\Scripts\activate   # On Windows

2. Install requirements
pip install -r requirements.txt

3. Run the application
streamlit run view.py

###References
This project leverages and adapts methods from:
Gaspar-Figueiredo, D.,  Fernández-Diego, M., Nuredini, R., Abrahao, S. and Insfran, E., 2024a. Reinforcement Learning-Based Framework for the Intelligent Adaptation of User Interfaces. In: M. Nebeling, L. D. Spano, J. D. Campos, eds. Companion Proceedings of the 16th ACM SIGCHI Symposium on Engineering Interactive Computing Systems (EICS '24 Companion), 24 - 28 June, 2024, Cagliari, Italy. New York: Association for Computing Machinery, pp. 40 - 48. Available from: https://doi.org/10.1145/3660515.3661329[Accessed 16 August 2025]. 
[Original GitHub Repository](https://github.com/RESQUELAB/RL-UIAdaptation)

All images in this prototype are taken from [pexels.com](https://www.pexels.com/), which provides free stock photos, royalty-free images, and videos shared by creators. 

###Disclaimer
This prototype was developed for academic research purposes only and is not intended for commercial use. 