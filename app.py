from flask import Flask, render_template, request, session, send_file, redirect, url_for
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "skillpath_secret_key"

CAREERS = {
    "data analyst": {
        "label": "📊 Data Analyst",
        "skills": ["python", "sql", "excel", "statistics", "power bi"]
    },
    "web developer": {
        "label": "💻 Web Developer",
        "skills": ["html", "css", "javascript", "python", "flask"]
    },
    "software developer": {
        "label": "🧑‍💻 Software Developer",
        "skills": ["python", "java", "sql", "git", "data structures"]
    },
    "data scientist": {
        "label": "🤖 Data Scientist",
        "skills": ["python", "sql", "statistics", "machine learning", "pandas"]
    }
}

LEVEL_WEIGHTS = {
    "Beginner": 0.50,
    "Intermediate": 0.75,
    "Advanced": 1.00
}

RESOURCES = {
    "python": "Learn Python fundamentals and build small projects.",
    "sql": "Practise SQL queries, joins and database operations.",
    "excel": "Learn formulas, charts and pivot tables.",
    "statistics": "Study probability and statistical concepts.",
    "power bi": "Learn dashboards, data modelling and visualisation.",
    "html": "Learn HTML tags and webpage structure.",
    "css": "Practise styling and responsive layouts.",
    "javascript": "Learn variables, functions and DOM manipulation.",
    "flask": "Build web applications using Python Flask.",
    "java": "Study Java programming and object-oriented concepts.",
    "git": "Learn Git commands and GitHub version control.",
    "data structures": "Practise arrays, stacks, queues and linked lists.",
    "machine learning": "Start with supervised and unsupervised learning.",
    "pandas": "Practise data analysis using Python Pandas."
}


def parse_skills(raw):
    skills = raw.replace("\n", ",").split(",")
    return list(dict.fromkeys(
        skill.strip().lower()
        for skill in skills
        if skill.strip()
    ))


def make_feedback(name, career, score, missing):
    person = name if name else "Student"

    if score >= 80:
        message = (
            f"Excellent work, {person}! Your skills show a strong "
            f"match with the {career} career."
        )
        advice = (
            "Focus on advanced projects, practical experience "
            "and interview preparation."
        )
    elif score >= 50:
        message = (
            f"Good progress, {person}! You already have a useful "
            f"foundation for becoming a {career}."
        )
        advice = (
            "Keep improving your missing skills and practise "
            "through small real-world projects."
        )
    else:
        message = (
            f"Keep going, {person}! Every expert starts somewhere. "
            f"You can build your path towards {career} step by step."
        )
        advice = (
            "Start with the basics, practise consistently "
            "and build one project at a time."
        )

    if missing:
        priorities = (
            "Your priority skills are: "
            + ", ".join(skill.title() for skill in missing[:3])
            + "."
        )
    else:
        priorities = (
            "You have covered all listed core skills. "
            "Now focus on advanced practice."
        )

    return f"{message} {priorities} {advice}"


@app.route("/", methods=["GET", "POST"])
def home():
    result = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        raw_skills = request.form.get("skills", "")
        entered_skills = parse_skills(raw_skills)

        level = request.form.get("level", "Beginner")
        if level not in LEVEL_WEIGHTS:
            level = "Beginner"

        career = request.form.get("target_job", "data analyst")
        if career not in CAREERS:
            career = "data analyst"

        required = CAREERS[career]["skills"]

        matched = [
            skill for skill in required
            if skill in entered_skills
        ]

        missing = [
            skill for skill in required
            if skill not in entered_skills
        ]

        total_score = sum(
            LEVEL_WEIGHTS[level] for skill in matched
        )

        score = round(
            (total_score / len(required)) * 100
        )

        if score >= 80:
            status = "Strong Match"
        elif score >= 50:
            status = "Good Progress"
        else:
            status = "Needs Improvement"

        breakdown = []

        for skill in required:
            is_matched = skill in entered_skills

            breakdown.append({
                "skill": skill.title(),
                "status": (
                    "Matched" if is_matched
                    else "Needs Improvement"
                ),
                "level": level if is_matched else "Not entered",
                "weight": (
                    f"{LEVEL_WEIGHTS[level] * 100:.0f}%"
                    if is_matched else "0%"
                ),
                "matched": is_matched
            })

        recommendations = [
            {
                "skill": skill.title(),
                "description": RESOURCES.get(
                    skill,
                    "Learn this skill through tutorials and practice."
                )
            }
            for skill in missing
        ]

        feedback = make_feedback(
            name,
            CAREERS[career]["label"],
            score,
            missing
        )

        result = {
            "name": name,
            "target_job": career,
            "career_label": CAREERS[career]["label"],
            "level": level,
            "matched": matched,
            "missing": missing,
            "breakdown": breakdown,
            "score": score,
            "status": status,
            "feedback": feedback,
            "recommendations": recommendations
        }

        session["report_data"] = result

    return render_template(
        "index.html",
        careers=CAREERS,
        result=result
    )


@app.route("/download_report")
def download_report():
    data = session.get("report_data")

    if not data:
        return redirect(url_for("home"))

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    pdf.setFillColor(colors.HexColor("#6842B8"))
    pdf.rect(0, height - 100, width, 100, fill=1)

    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 21)
    pdf.drawString(40, height - 55, "SkillPath Report")

    y = height - 135
    pdf.setFillColor(colors.black)

    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(40, y, "Student Details")
    y -= 25

    pdf.setFont("Helvetica", 10)

    details = [
        f"Name: {data['name'] or 'Student'}",
        f"Target Career: {data['career_label']}",
        f"Skill Level: {data['level']}",
        f"Skill Match: {data['score']}%",
        f"Career Status: {data['status']}",
        f"Report Date: {datetime.now().strftime('%d-%m-%Y')}"
    ]

    for line in details:
        pdf.drawString(45, y, line)
        y -= 18

    y -= 12
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(40, y, "Skill Breakdown")
    y -= 23

    pdf.setFont("Helvetica", 9)

    for item in data["breakdown"]:
        if y < 60:
            pdf.showPage()
            y = height - 55
            pdf.setFont("Helvetica", 9)

        line = (
            f"{item['skill']} - {item['status']} - "
            f"Level: {item['level']} - Weight: {item['weight']}"
        )
        pdf.drawString(45, y, line)
        y -= 16

    y -= 15

    if y < 100:
        pdf.showPage()
        y = height - 55

    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(40, y, "Personalised Feedback")
    y -= 22

    pdf.setFont("Helvetica", 9)

    words = data["feedback"].split()
    line = ""

    for word in words:
        test_line = (line + " " + word).strip()

        if pdf.stringWidth(test_line, "Helvetica", 9) > width - 90:
            pdf.drawString(45, y, line)
            y -= 14
            line = word
        else:
            line = test_line

    if line:
        pdf.drawString(45, y, line)
        y -= 25

    if data["recommendations"]:
        if y < 90:
            pdf.showPage()
            y = height - 55

        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(40, y, "Learning Roadmap")
        y -= 22

        pdf.setFont("Helvetica", 9)

        for item in data["recommendations"]:
            if y < 60:
                pdf.showPage()
                y = height - 55
                pdf.setFont("Helvetica", 9)

            pdf.drawString(
                45, y,
                f"{item['skill']}: {item['description'][:100]}"
            )
            y -= 17

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="SkillPath_Report.pdf",
        mimetype="application/pdf"
    )


if __name__ == "__main__":
    app.run(debug=True)