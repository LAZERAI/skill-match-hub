import mysql.connector
import json

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Rijin@1234",
    database="resume_db"
)

cursor = conn.cursor()

with open("resume_metadata.json", "r", encoding="utf-8") as f:
    resumes = json.load(f)

query = """
INSERT INTO resumes (
    resume_id, filename, file_path, text,
    name, email, skills,
    experience_years, internship_years, total_experience_years
)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
"""

for r in resumes:

    meta = r.get("metadata", {})

    values = (
        r.get("resume_id"),
        r.get("filename"),
        r.get("file_path"),
        r.get("text"),

        meta.get("name"),
        meta.get("email"),
        ", ".join(meta.get("skills", [])),

        meta.get("experience_years", 0),
        meta.get("internship_years", 0),
        meta.get("total_experience_years", 0)
    )

    cursor.execute(query, values)

conn.commit()

print("All resumes inserted successfully!")

cursor.close()
conn.close()