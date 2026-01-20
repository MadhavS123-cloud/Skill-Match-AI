from flask import Flask, render_template, request
from models.resume_ranker import rank_resumes

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    results = None

    if request.method == "POST":
        job_description = request.form["job_description"]

        resumes_text = [
            r.strip()
            for r in request.form["resumes"].split("\n\n")
            if r.strip()
        ]

        ranked = rank_resumes(resumes_text, job_description)

        results = [
            {
                "resume_no": idx + 1,
                "score": round(score[0] * 100, 2)
            }
            for idx, score in ranked
        ]

    return render_template("index.html", results=results)

if __name__ == "__main__":
    app.run(debug=True)
