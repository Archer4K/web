from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from groq import Groq

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Change this to a random secret key

# Configure the database
import os
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'instance', 'users.db')  # Use SQLite database
db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Create the database tables
with app.app_context():
    db.create_all()

@app.route("/", methods=["GET", "POST"])
def index():
    if "username" in session:
        return render_template("signedin.html")
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Username already exists"

        # Create a new user
        new_user = User(username=username)
        new_user.set_password(password)

        # Add the user to the database
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("signin"))
    return render_template("index.html")

@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Find the user in the database
        user = User.query.filter_by(username=username).first()

        # Check if the user exists and the password is correct
        if user and user.check_password(password):
            # Store the user in the session
            session["username"] = username
            return render_template("signedin.html")
        return "Invalid username or password"
    return render_template("index.html")

@app.route("/step1")
def step1():
    return render_template("step1.html")

@app.route("/step2", methods=["POST"])
def step2():
    session["name"] = request.form["name"]
    session["gradeLevel"] = request.form["gradeLevel"]
    session["intendedMajor"] = request.form["intendedMajor"]
    session["unweightedGPA"] = request.form["unweightedGPA"]
    return render_template("step2.html")

@app.route("/step3", methods=["POST"])
def step3():
    session["class1"] = request.form["class1"]
    session["class2"] = request.form["class2"]
    session["class3"] = request.form["class3"]
    return render_template("step3.html")

@app.route("/step4", methods=["POST"])
def step4():
    session["activityName1"] = request.form["activityName1"]
    session["activityDescription1"] = request.form["activityDescription1"]
    session["hoursPerWeek1"] = request.form["hoursPerWeek1"]
    return render_template("step4.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    session["hobbiesAndInterests"] = request.form["hobbiesAndInterests"]
    session["shortTermGoals"] = request.form["shortTermGoals"]
    session["longTermGoals"] = request.form["longTermGoals"]

    profile_data = {
        "name": session.get("name"),
        "gradeLevel": session.get("gradeLevel"),
        "intendedMajor": session.get("intendedMajor"),
        "unweightedGPA": session.get("unweightedGPA"),
        "classes": [session.get("class1"), session.get("class2"), session.get("class3")],
        "activities": [{"name": session.get("activityName1"), "description": session.get("activityDescription1"), "hoursPerWeek": session.get("hoursPerWeek1")}],
        "hobbiesAndInterests": session.get("hobbiesAndInterests"),
        "shortTermGoals": session.get("shortTermGoals"),
        "longTermGoals": session.get("longTermGoals"),
    }

    # Call Groq API
    from groq import Groq

    api_key = "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"
    client = Groq(api_key=api_key)

    gpa = session.get("unweightedGPA")
    major = session.get("intendedMajor")
    classes = ", ".join([session.get("class1"), session.get("class2"), session.get("class3")] or [])
    hobbies = session.get("hobbiesAndInterests")
    activities = session.get("activityDescription1")

    prompt = f"""
    You are a highly experienced college admissions counselor providing a comprehensive analysis to a high school student. Your goal is to provide actionable insights and recommendations to strengthen their college application.

    Consider the following academic profile:
    - GPA: {gpa}
    - Intended Major: {major}
    - Relevant Classes: {classes}
    - Extracurricular Activities: {activities or "None listed"}
    - Interests and Hobbies: {hobbies or "None listed"}

    Based on this information, provide a detailed report with the following sections:

    Strengths:
    - Identify 2-3 key strengths of the student's profile related to their academics and extracurricular involvement.
    - Provide specific examples and explain why these are valuable for college admissions.

    Weaknesses:
    - Identify 2-3 areas where the student's profile could be improved. Be direct but constructive.
    - Explain the potential impact of these weaknesses on their college applications.

    Recommendations:
    - Provide 3-5 actionable recommendations to enhance the student's profile. Each recommendation should include:
        - A specific action to take.
        - An estimated time commitment per week.
        - Relevant resources (e.g., websites, programs, competitions).
        - Format each recommendation as: "[Action] - [Time commitment] - [Resources]"

    Short-Term Goals:
    - Define 2-3 realistic and measurable short-term goals (within the next 6-12 months) that align with the recommendations.
    - These goals should help the student address their weaknesses and build upon their strengths.
    - Format each goal as: "[Goal description]"

    Long-Term Goals:
    - Define 2-3 ambitious but achievable long-term goals (over the next 2-3 years) that will significantly enhance the student's college application.
    - These goals should reflect a commitment to academic excellence, personal growth, and meaningful engagement in their chosen field.
    - Format each goal as: "[Goal description]"

    Remember to provide concrete advice, specific tools and resources, and actionable next steps. Maintain a tone that is both encouraging and insightful, similar to a professional college admissions coach.
    """

    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=1,
        max_completion_tokens=1024,
        top_p=1,
        stream=False,
        stop=None,
    )

    analysis_result = completion.choices[0].message.content
 
    import re
    strengths = re.search(r"Strengths:\s*([\s\S]*?)Weaknesses:", analysis_result, re.DOTALL)
    weaknesses = re.search(r"Weaknesses:\s*([\s\S]*?)Recommendations:", analysis_result, re.DOTALL)
    recommendations = re.search(r"Recommendations:\s*([\s\S]*?)Short-Term Goals:", analysis_result, re.DOTALL)
    short_term_goals = re.search(r"Short-Term Goals:\s*([\s\S]*?)Long-Term Goals:", analysis_result, re.DOTALL)
    long_term_goals = re.search(r"Long-Term Goals:\s*([\s\S]*)", analysis_result, re.DOTALL)
 
    strengths = strengths.group(1).strip() if strengths and strengths.group(1) else "No strengths found."
    weaknesses = weaknesses.group(1).strip().replace("*", "") if weaknesses and weaknesses.group(1) else "No weaknesses found."
    recommendations = recommendations.group(1).strip().replace("*", "") if recommendations and recommendations.group(1) else "No recommendations found."
    short_term_goals = short_term_goals.group(1).strip().replace("*", "") if short_term_goals and short_term_goals.group(1) else "No short-term goals found."
    long_term_goals = long_term_goals.group(1).strip() if long_term_goals and long_term_goals.group(1) else "No long-term goals found."
 
    strengths = "\\n".join([s.strip() for s in strengths.replace("*", "").split("\\n")])
    weaknesses = "\\n".join([w.strip() for w in weaknesses.replace("*", "").split("\\n")])
    recommendations = "\\n".join([r.strip() for r in recommendations.replace("*", "").split("\\n") if r.strip()])
    short_term_goals = "\\n".join([st.strip() for st in short_term_goals.replace("*", "").split("\\n")])
    long_term_goals = "\\n".join([lt.strip() for lt in long_term_goals.replace("*", "").split("\\n")])
 
    session.clear()
 
    return render_template(
        "analysis.html",
        strengths=strengths,
        weaknesses=weaknesses,
        recommendations=recommendations,
        short_term_goals=short_term_goals,
        long_term_goals=long_term_goals,
    )

@app.route("/save_recommendations", methods=["POST"])
def save_recommendations():
    checked_recommendations = request.form.getlist("recommendations")
    session["checked_recommendations"] = checked_recommendations
    return "Recommendations saved!"

if __name__ == "__main__":
    app.run(debug=True)