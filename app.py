import streamlit as st
import random
import os
import shutil
import smtplib
from email.message import EmailMessage

# ==========================================
# DATA & CONFIGURATION
# ==========================================
# We now pull the email credentials from Streamlit's secure "Secrets" vault
# so they are never visible in the code itself!
TEACHER_RECEIVING_EMAIL = "rohitkrchrtri@gmail.com"

capitals = {
    'Alabama': 'Montgomery', 'Alaska': 'Juneau', 'Arizona': 'Phoenix',
    'Arkansas': 'Little Rock', 'California': 'Sacramento', 'Colorado': 'Denver',
    'Connecticut': 'Hartford', 'Delaware': 'Dover', 'Florida': 'Tallahassee',
    'Georgia': 'Atlanta', 'Hawaii': 'Honolulu', 'Idaho': 'Boise',
    'Illinois': 'Springfield', 'Indiana': 'Indianapolis', 'Iowa': 'Des Moines',
    'Kansas': 'Topeka', 'Kentucky': 'Frankfort', 'Louisiana': 'Baton Rouge',
    'Maine': 'Augusta', 'Maryland': 'Annapolis', 'Massachusetts': 'Boston',
    'Michigan': 'Lansing', 'Minnesota': 'Saint Paul', 'Mississippi': 'Jackson',
    'Missouri': 'Jefferson City', 'Montana': 'Helena', 'Nebraska': 'Lincoln',
    'Nevada': 'Carson City', 'New Hampshire': 'Concord', 'New Jersey': 'Trenton',
    'New Mexico': 'Santa Fe', 'New York': 'Albany', 'North Carolina': 'Raleigh',
    'North Dakota': 'Bismarck', 'Ohio': 'Columbus', 'Oklahoma': 'Oklahoma City',
    'Oregon': 'Salem', 'Pennsylvania': 'Harrisburg', 'Rhode Island': 'Providence',
    'South Carolina': 'Columbia', 'South Dakota': 'Pierre', 'Tennessee': 'Nashville',
    'Texas': 'Austin', 'Utah': 'Salt Lake City', 'Vermont': 'Montpelier',
    'Virginia': 'Richmond', 'Washington': 'Olympia', 'West Virginia': 'Charleston',
    'Wisconsin': 'Madison', 'Wyoming': 'Cheyenne'
}

# ==========================================
# EMAIL FUNCTION (Runs on the Server)
# ==========================================
def generate_files_and_email(student_name, score, percentage, test_results):
    safe_name = student_name.replace(" ", "_")
    folder_name = f"{safe_name}_Submission"
    os.makedirs(folder_name, exist_ok=True)
    
    # Write files
    with open(os.path.join(folder_name, f"{safe_name}_Submission.txt"), "w") as f:
        f.write(f"Student: {student_name}\nScore: {score}/10 ({percentage}%)\n\n")
        for i, r in enumerate(test_results):
            f.write(f"Q{i+1}: Capital of {r['state']}? Student Guessed: {r['student_guess']} | Correct: {r['correct']}\n")

    # Zip files
    shutil.make_archive(folder_name, 'zip', folder_name)
    zip_filename = f"{folder_name}.zip"

    # Send Email securely using st.secrets
    try:
        msg = EmailMessage()
        msg['Subject'] = f"New Web Quiz Submission: {student_name} ({score}/10)"
        msg['From'] = st.secrets["BOT_EMAIL_ADDRESS"]
        msg['To'] = TEACHER_RECEIVING_EMAIL
        msg.set_content(f"Score: {percentage}%\nAttached is the submission.")

        with open(zip_filename, 'rb') as z:
            msg.add_attachment(z.read(), maintype='application', subtype='zip', filename=zip_filename)

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(st.secrets["BOT_EMAIL_ADDRESS"], st.secrets["BOT_APP_PASSWORD"])
            server.send_message(msg)
            
        success = True
    except Exception as e:
        st.error(f"Failed to send email. Error: {e}")
        success = False

    # Cleanup server files
    shutil.rmtree(folder_name, ignore_errors=True)
    if os.path.exists(zip_filename):
        os.remove(zip_filename)

    return success

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
# This tells the web app to remember these variables even when the page reloads
if 'step' not in st.session_state:
    st.session_state.step = 'login'
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'current_q' not in st.session_state:
    st.session_state.current_q = 0
if 'results' not in st.session_state:
    st.session_state.results = []
if 'quiz_data' not in st.session_state:
    # Generate all 10 questions upfront so they don't reshuffle on every click
    states = list(capitals.keys())
    random.shuffle(states)
    questions = []
    for state in states[:10]:
        correct = capitals[state]
        wrong = list(capitals.values())
        wrong.remove(correct)
        options = random.sample(wrong, 3) + [correct]
        random.shuffle(options)
        questions.append({'state': state, 'correct': correct, 'options': options})
    st.session_state.quiz_data = questions

# ==========================================
# USER INTERFACE
# ==========================================
st.title("🏛️ US State Capitals Quiz")

# --- STEP 1: LOGIN ---
if st.session_state.step == 'login':
    st.write("Welcome! This quiz works perfectly on your phone or computer.")
    student_name = st.text_input("Enter your full name to begin:")
    
    if st.button("Start Quiz"):
        if student_name.strip() == "":
            st.warning("Please enter your name!")
        else:
            st.session_state.student_name = student_name
            st.session_state.step = 'quiz'
            st.rerun()

# --- STEP 2: THE QUIZ ---
elif st.session_state.step == 'quiz':
    q_index = st.session_state.current_q
    q_data = st.session_state.quiz_data[q_index]
    
    st.progress((q_index) / 10) # Shows a nice progress bar at the top
    st.subheader(f"Question {q_index + 1} of 10")
    st.write(f"**What is the capital of {q_data['state']}?**")
    
    # Radio buttons for mobile-friendly tapping
    choice = st.radio("Select an answer:", q_data['options'], index=None)
    
    if st.button("Submit Answer"):
        if choice is None:
            st.warning("Please select an answer before continuing.")
        else:
            # Check answer and record it
            is_correct = (choice == q_data['correct'])
            if is_correct:
                st.session_state.score += 1
                
            st.session_state.results.append({
                'state': q_data['state'],
                'student_guess': choice,
                'correct': q_data['correct'],
                'is_correct': is_correct
            })
            
            # Move to next question or finish
            if st.session_state.current_q < 9:
                st.session_state.current_q += 1
                st.rerun()
            else:
                st.session_state.step = 'results'
                st.rerun()

# --- STEP 3: RESULTS & SUBMISSION ---
elif st.session_state.step == 'results':
    st.success("Quiz Complete!")
    percentage = round((st.session_state.score / 10) * 100)
    
    st.markdown(f"### Great job, {st.session_state.student_name}!")
    st.markdown(f"## Your Score: {st.session_state.score}/10 ({percentage}%)")
    
    # We use a spinner so the user knows the app is sending the email
    with st.spinner("Submitting test to your teacher..."):
        # We only send the email ONCE, checking if it was already sent
        if 'email_sent' not in st.session_state:
            success = generate_files_and_email(
                st.session_state.student_name, 
                st.session_state.score, 
                percentage, 
                st.session_state.results
            )
            st.session_state.email_sent = success
            
    if st.session_state.email_sent:
        st.info("✅ Your graded paper has been securely sent to your teacher. You may close this tab.")
    else:
        st.error("There was a problem sending your test. Please notify your teacher.")
