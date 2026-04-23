#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      ANANYA SRI TK
#
# Created:     23-04-2026
# Copyright:   (c) ANANYA SRI TK 2026
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import csv
import random

first_names = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Krish", "Ishaan", "Reyansh", "Kabir",
    "Aanya", "Diya", "Anaya", "Myra", "Saanvi", "Kiara", "Anika", "Riya", "Ira", "Meera",
    "Rahul", "Sneha", "Asha", "Priya", "Kiran", "Nikhil", "Pooja", "Rohan", "Isha", "Tanvi",
    "Harsha", "Varun", "Tejas", "Manya", "Navya", "Akash", "Neha", "Dev", "Siddhi", "Aryan",
    "Nandini", "Yash", "Lavanya", "Bhavya", "Suhani", "Manas", "Om", "Ritika", "Ved", "Shreya"
]

last_names = [
    "Sharma", "Reddy", "Verma", "Mehta", "Patel", "Rao", "Nair", "Iyer", "Kapoor", "Jain",
    "Gupta", "Yadav", "Singh", "Das", "Kulkarni", "Chopra", "Bhat", "Mishra", "Saxena", "Pillai",
    "Agarwal", "Joshi", "Menon", "Mukherjee", "Naidu", "Choudhary", "Pandey", "Malhotra", "Soni", "Bose"
]

classes = ["CSE", "ECE", "EEE", "MECH", "CIVIL", "IT"]
sections = ["A", "B", "C", "D"]
subjects = ["Math", "Physics", "Chemistry", "Programming", "English"]
months = ["Jan", "Feb", "Mar"]

def bounded(val, low, high):
    return max(low, min(high, int(val)))

students = []
used_names = set()

target_students = 2200

while len(students) < target_students:
    name = random.choice(first_names) + " " + random.choice(last_names)
    # allow duplicate names across different IDs, just not exact same tuple too often
    student_id = 100001 + len(students)
    class_name = random.choice(classes)
    section = random.choice(sections)
    students.append((student_id, name, class_name, section))

rows = []

for student_id, student, class_name, section in students:
    performance_type = random.choice(["high", "mid", "low", "improving", "dropping", "mismatch"])
    base_attendance = random.randint(60, 98)

    for month_index, month in enumerate(months):
        for subject in subjects:
            if performance_type == "high":
                base_mark = random.randint(80, 95)
            elif performance_type == "mid":
                base_mark = random.randint(60, 79)
            elif performance_type == "low":
                base_mark = random.randint(35, 59)
            elif performance_type == "improving":
                base_mark = 50 + month_index * 10 + random.randint(-5, 5)
            elif performance_type == "dropping":
                base_mark = 88 - month_index * 10 + random.randint(-5, 5)
            else:  # mismatch
                base_mark = random.choice([random.randint(40, 58), random.randint(84, 96)])

            marks = bounded(base_mark + random.randint(-6, 6), 30, 100)

            if performance_type == "mismatch":
                if marks < 60:
                    attendance = random.randint(88, 98)
                else:
                    attendance = random.randint(55, 72)
            else:
                attendance = bounded(base_attendance + random.randint(-7, 7), 50, 100)

            rows.append([
                student_id,
                student,
                class_name,
                section,
                subject,
                marks,
                attendance,
                month
            ])

with open("data.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["StudentID", "Student", "Class", "Section", "Subject", "Marks", "Attendance", "Month"])
    writer.writerows(rows)

print("data.csv created successfully")
print("Students:", len(students))
print("Rows:", len(rows))