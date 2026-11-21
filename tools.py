"""
Tool implementations for PUCIT BS(CS) Conversation Advisor Agent
"""
COURSES = {
    1: [
        ("MS-251", "Probability & Statistics", 3.0),
        ("GE-160", "Applications of ICT", 3.0),
        ("GE-169", "Applied Physics", 3.0),
        ("GE-167", "Discrete Structures", 3.0),
        ("HQ-001", "Quran Translation I", 0.5),
        ("GE-190", "Functional English", 3.0),
    ],
    2: [
        ("CC-112", "Programming Fundamentals", 3.0),
        ("CC-112-L", "Programming Fundamentals Lab", 1.0),
        ("CC-110", "Digital Logic Design", 2.0),
        ("CC-110-L", "Digital Logic Design Lab", 1.0),
        ("MS-252", "Linear Algebra", 3.0),
        ("GE-191", "Expository Writing", 3.0),
        ("GE-163", "Islamic Studies", 2.0),
        ("HQ-002", "Quran Translation II", 0.5),
    ],
    3: [
        ("CC-211", "Object Oriented Programming", 3.0),
        ("CC-211-L", "Object Oriented Programming Lab", 1.0),
        ("CC-215", "Database Systems", 3.0),
        ("CC-215-L", "Database Systems Lab", 1.0),
        ("CC-210", "Computer Organization & Assembly Language", 3.0),
        ("GE-162", "Calculus & Analytical Geometry", 3.0),
        ("GE-192", "Introduction to Management", 2.0),
        ("HQ-003", "Quran Translation III", 0.5),
    ],
    4: [
        ("CC-213", "Data Structures", 3.0),
        ("CC-213-L", "Data Structures Lab", 1.0),
        ("CC-312", "Information Security", 3.0),
        ("CC-214", "Computer Networks", 3.0),
        ("CC-212", "Software Engineering", 3.0),
        ("DC-220", "Advanced Database Management Systems", 3.0),
        ("HQ-004", "Quran Translation IV", 0.5),
    ],
    5: [
        ("CC-313", "Analysis of Algorithms", 3.0),
        ("CC-310", "Artificial Intelligence", 3.0),
        ("DC-320", "Theory of Automata and Formal Languages", 3.0),
        ("DC-321", "Human Computer Interaction", 3.0),
        ("DC-322", "Computer Architecture", 3.0),
        ("EC-330", "Web Technologies / Elective", 3.0),
        ("HQ-005", "Quran Translation V", 0.5),
    ],
    6: [
        ("CC-311", "Operating Systems", 3.0),
        ("EC-333", "Mobile Application Development / Elective", 3.0),
        ("EC-324", "Software Construction & Development / Elective", 3.0),
        ("EC-335", "Machine Learning / Elective", 3.0),
        ("EC-334", "Game Design and Development / Elective", 3.0),
        ("MS-253", "Multivariable Calculus", 3.0),
        ("HQ-006", "Quran Translation VI", 0.5),
    ],
    7: [
        ("CC-411", "Final Year Project I", 2.0),
        ("DC-328", "Parallel & Distributed Computing", 3.0),
        ("EC-345", "Computer Vision / Elective", 3.0),
        ("EC-425", "Software Quality Engineering / Elective", 3.0),
        ("MS-254", "Technical and Business Writing", 3.0),
        ("GE-263", "Entrepreneurship", 2.0),
        ("GE-262", "Professional Practices", 2.0),
        ("HQ-007", "Quran Translation VII", 0.5),
    ],
    8: [
        ("CC-412", "Final Year Project II", 4.0),
        ("DC-421", "Compiler Construction", 3.0),
        ("UE-272", "Introduction to Marketing", 3.0),
        ("GE-168", "Ideology and Constitution of Pakistan", 2.0),
        ("GE-363", "Civics and Community Engagement", 2.0),
        ("HQ-008", "Quran Translation VIII", 0.5),
    ],
}

def marks_to_grade_points(marks: int) -> float | str:
    """Convert percentage/marks to GPA using this"""

    if (marks<0 or marks >100):
        return "Error: marks must be between 0 and 100."

    if (marks >= 85):
        return 4.0
    elif (marks >= 80):
        return 3.7
    elif (marks >= 75):
        return 3.3
    elif (marks >= 70):
        return 3.0
    elif (marks >= 65):
        return 2.7
    elif (marks >= 61):
        return 2.3
    elif (marks >= 58):
        return 2.0
    elif (marks >= 55):
        return 1.7
    elif (marks >= 50):
        return 1.0
    else:
        return 0.0

def calculate_semester_gpa(grade_points: list[float], credit_hours: list[float]) -> float | str:
    """To calculate a single semester's GPA given a list of grade points and corresponding credit hours"""
    if (len(grade_points) != len(credit_hours)):
        return "Error: grade_points and credit_hours lists must have the same length"

    if not credit_hours or sum(credit_hours) == 0:
        return "Error: Total credit hours must be greater than zero"

    total_weighted_points = 0.0
    for i in range(len(grade_points)):
        total_weighted_points += grade_points[i] * credit_hours[i]

    total_credit_hours = sum(credit_hours)
    return round(total_weighted_points / total_credit_hours, 2)


def calculate_new_cgpa(current_cgpa: float, completed_credit_hours: float, semester_gpa: float,semester_credit_hours: float) -> float | str:
    """To calculate a new cumulative CGPA after completing a semester with a specific GPA"""
    if not (0.0 <= current_cgpa <= 4.0) or not (0.0 <= semester_gpa <= 4.0):
        return "Error: CGPA and GPA values must be between 0.0 and 4.0"

    total_ch = completed_credit_hours + semester_credit_hours
    if total_ch == 0:
        return "Error: total credit hours cannot be zero"

    new_cgpa = ((current_cgpa * completed_credit_hours) + (semester_gpa * semester_credit_hours)) / total_ch
    return round(new_cgpa, 2)


def required_gpa_for_target(target_cgpa: float,current_cgpa: float,completed_credit_hours: float,remaining_credit_hours: float) -> float | str:
    """To calculate the required GPA needed across remaining credit hours to achieve a target CGPA"""
    if not (0.0 <= current_cgpa <= 4.0) or not (0.0 <= target_cgpa <= 4.0):
        return "Error: CGPA values must be between 0.0 and 4.0"

    if remaining_credit_hours <= 0:
        return "Error: remaining credit hours must be greater than zero"

    total_ch = completed_credit_hours + remaining_credit_hours
    req_gpa = ((target_cgpa * total_ch) - (current_cgpa * completed_credit_hours)) / remaining_credit_hours
    return round(req_gpa, 2)

def get_semester_courses(semester: int) -> str:
    """To get list of official courses, course codes, and credit hours for a given PUCIT BS(CS) semester (1 to 8)"""
    if semester not in COURSES:
        return "Error: semester must be between 1 and 8"

    total_ch = 0.0
    result=f"Semester {semester} Courses:\n"
    total_ch = 0.0

    for course in COURSES[semester]:
        code = course[0]
        title = course[1]
        ch = course[2]
        result += f"- {code}: {title} ({ch} CH)\n"
        total_ch += ch

    result += f"Total Semester Credit Hours: {total_ch}"
    return result
    

def get_remaining_credit_hours(current_semester: int) -> float | str:
    """To calculate total remaining graded credit hours from current_semester onwards up to semester 8"""
    if not (1 <= current_semester <= 8):
        return "Error: semester must be between 1 and 8"

    total_remaining = 0.0
    for sem in range(current_semester, 9):  
        for course in COURSES[sem]:         
            total_remaining += course[2]     

    return total_remaining

def save_report(filename: str, content: str) -> str:
    """To save a final summary report to a text file when the user explicitly asks to save their results"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Report successfully saved to '{filename}'."
    except Exception as e:
        return f"Error: failed to save report. Detail: {str(e)}"