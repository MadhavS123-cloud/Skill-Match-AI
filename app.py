from flask import Flask, render_template, request
from models.resume_ranker import rank_resumes

app = Flask(__name__)   # ✅ app MUST be created BEFORE routes


@app.route("/", methods=["GET", "POST"])
def index():
    results = None

    if request.method == "POST":
        job_description = request.form["job_description"]

        raw_resumes = request.form["resumes"]

        resumes_text = [
            r.strip()
            for r in raw_resumes.split("\r\n\r\n")
            if r.strip()
        ]

        # Debug line (temporary)
        print("Number of resumes:", len(resumes_text))

        ranked = rank_resumes(resumes_text, job_description)

        results = [
            {
                "resume_no": idx + 1,
                "score": round(min(score[0] * 100, 100), 2)
            }
            for idx, score in ranked
        ]

    return render_template("index.html", results=results)


if __name__ == "__main__":
    app.run(debug=True)
