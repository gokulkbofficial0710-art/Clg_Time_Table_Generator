import io
from typing import List, Dict, Any, Optional
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_timetable_pdf(
    assignments: List[Dict[str, Any]],
    timetable_name: str,
    metrics: Dict[str, Any] = None,
    report_type: str = "master" # "master", "room", "student"
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        spaceAfter=14
    )
    cell_style = ParagraphStyle(
        "Cell",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1e293b")
    )
    cell_bold_style = ParagraphStyle(
        "CellBold",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f172a")
    )

    elements = []

    # Title Banner
    report_title = "The Exam Timetable from Hell — Official Examination Schedule"
    if report_type == "room":
        report_title = "Examination Schedule — Room-Wise Allocations"
    elif report_type == "student":
        report_title = "Examination Schedule — Student Cohort Allocations"

    elements.append(Paragraph(report_title, title_style))
    
    subtext = f"Schedule Version: <b>{timetable_name}</b> | Generated at: 2026-10-09"
    if metrics and "quality_score" in metrics:
        subtext += f" | Quality Score: <b>{metrics['quality_score']}/100</b> | Solver Status: <b>{metrics.get('solver_status', 'FEASIBLE')}</b>"
    elements.append(Paragraph(subtext, subtitle_style))
    elements.append(Spacer(1, 8))

    # Table Header
    headers = ["Exam Code", "Course Title", "Department", "Date", "Time Window", "Period", "Room", "Building", "Capacity", "Students", "Status"]
    table_data = [[Paragraph(f"<b>{h}</b>", cell_bold_style) for h in headers]]

    # Sort assignments by Date then Start Time
    sorted_assignments = sorted(
        assignments,
        key=lambda a: (a.get("date") or "", a.get("start_time") or "", a.get("exam_code") or "")
    )

    for a in sorted_assignments:
        status_badge = "Locked" if a.get("is_locked") else ("Scheduled" if a.get("timeslot_id") else "Unscheduled")
        row = [
            Paragraph(a.get("exam_code", "-"), cell_bold_style),
            Paragraph(a.get("course_name", "-")[:30], cell_style),
            Paragraph(a.get("department", "-"), cell_style),
            Paragraph(str(a.get("date", "-")), cell_style),
            Paragraph(f"{a.get('start_time', '')} - {a.get('end_time', '')}", cell_style),
            Paragraph(a.get("period", "-"), cell_style),
            Paragraph(a.get("room_code", "TBA"), cell_bold_style),
            Paragraph(a.get("building", "-")[:20], cell_style),
            Paragraph(str(a.get("room_capacity", "-")), cell_style),
            Paragraph(str(a.get("assigned_student_count", 0)), cell_style),
            Paragraph(status_badge, cell_style),
        ]
        table_data.append(row)

    col_widths = [75, 140, 90, 65, 80, 55, 65, 85, 45, 45, 55]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    elements.append(t)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def generate_department_seatings_pdf(
    department: Optional[str],
    students_seatings: List[Dict[str, Any]],
    timetable_name: str,
    metrics: Optional[Dict[str, Any]] = None
) -> bytes:
    """
    Generates an official Department-Wise Student Seating & Examination Hall Allocations ledger.
    Shows each student in the department, their 5 (or N) subjects, exam dates, timings,
    assigned examination rooms/halls, and individual desk numbers.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=32,
        leftMargin=32,
        topMargin=32,
        bottomMargin=32
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DeptTitle",
        parent=styles["Heading1"],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=3
    )
    subtitle_style = ParagraphStyle(
        "DeptSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#475569"),
        spaceAfter=10
    )
    student_banner_style = ParagraphStyle(
        "StudentBanner",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f172a")
    )
    student_sub_style = ParagraphStyle(
        "StudentSub",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#334155")
    )
    cell_style = ParagraphStyle(
        "CellNormal",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1e293b")
    )
    cell_bold = ParagraphStyle(
        "CellBold",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f172a")
    )
    cell_seat = ParagraphStyle(
        "CellSeat",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1d4ed8") # Blue badge color
    )

    elements = []

    # Title & Metadata Banner
    dept_label = department if department else "All Academic Departments"
    elements.append(Paragraph(f"Official Student Seating & Examination Hall Roster", title_style))
    
    meta_parts = [
        f"<b>Department:</b> {dept_label}",
        f"<b>Timetable Version:</b> {timetable_name}",
        f"<b>Total Candidates:</b> {len(students_seatings)}",
        "<b>Academic Term:</b> Fall 2026",
    ]
    if metrics and "quality_score" in metrics:
        meta_parts.append(f"<b>Schedule Quality:</b> {metrics['quality_score']}/100")
        meta_parts.append(f"<b>Clashes:</b> {metrics.get('hard_violations_count', 0)}")
    
    elements.append(Paragraph(" &nbsp;|&nbsp; ".join(meta_parts), subtitle_style))
    elements.append(Spacer(1, 6))

    if not students_seatings:
        elements.append(Paragraph("<i>No student seating records found for this selection.</i>", cell_style))
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    # Iterate over students and output each student with their exam seatings
    for idx, student in enumerate(students_seatings):
        student_elements = []

        # Student Summary Header Bar
        s_id = student.get("student_id", "-")
        s_name = student.get("name", "-")
        s_dept = student.get("department", "-")
        s_sem = student.get("semester", "-")
        exams = student.get("exams", [])
        accommodations = student.get("special_accommodations", [])
        acc_text = f" [Acc: {', '.join(accommodations)}]" if accommodations else ""

        banner_text = (
            f"<b>#{idx+1}. {s_name}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>ID:</b> {s_id} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Dept:</b> {s_dept} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Semester:</b> {s_sem} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Enrolled Subjects:</b> {len(exams)}{acc_text}"
        )

        header_table = Table(
            [[Paragraph(banner_text, student_banner_style)]],
            colWidths=[720],
            rowHeights=[20]
        )
        header_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#e2e8f0")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("LINEBELOW", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ]))
        student_elements.append(header_table)

        # Exam Table for this student
        exam_headers = ["Sl", "Course Code", "Course Title", "Exam Date", "Day", "Time Window", "Hall / Room", "Building Venue", "Allocated Seat"]
        exam_rows = [[Paragraph(f"<b>{h}</b>", cell_bold) for h in exam_headers]]

        for e_idx, e in enumerate(exams):
            exam_rows.append([
                Paragraph(str(e_idx + 1), cell_style),
                Paragraph(e.get("course_code", "-"), cell_bold),
                Paragraph(e.get("course_name", "-")[:32], cell_style),
                Paragraph(str(e.get("date", "-")), cell_style),
                Paragraph(e.get("day_name", "-"), cell_style),
                Paragraph(f"{e.get('start_time', '')} - {e.get('end_time', '')}", cell_style),
                Paragraph(e.get("room_code", "TBA"), cell_bold),
                Paragraph(e.get("building", "-")[:22], cell_style),
                Paragraph(e.get("seat_number", "Allocated"), cell_seat),
            ])

        col_widths = [24, 70, 160, 68, 60, 84, 74, 96, 84]
        exam_table = Table(exam_rows, colWidths=col_widths)
        exam_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fcfcfd")]),
        ]))
        student_elements.append(exam_table)
        student_elements.append(Spacer(1, 10))

        # Keep student header and exams together when possible
        elements.append(KeepTogether(student_elements))

    # Official sign-off block at end of report
    elements.append(Spacer(1, 12))
    sign_table_data = [
        [
            Paragraph("<b>Generated by Registrar Academic Office</b><br/>Office of Examination Timetabling", cell_style),
            Paragraph("<b>Verified by Faculty Dean</b><br/>Department Head Authentication", cell_style),
            Paragraph("<b>Controller of Examinations</b><br/>Official University Seal & Approval", cell_style),
        ]
    ]
    sign_table = Table(sign_table_data, colWidths=[240, 240, 240])
    sign_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, -1), 1, colors.HexColor("#94a3b8")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(sign_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def generate_student_hall_ticket_pdf(
    student_data: Dict[str, Any],
    exams_seatings: List[Dict[str, Any]],
    timetable_name: str
) -> bytes:
    """
    Generates a personalized, official Student Examination Admit Card / Hall Ticket (Portrait Letter).
    Contains:
    - University Header & Examination Office Insignia
    - Candidate Identification Profile
    - Registered 5-Subject Examination Timings, Dates, Venues & Assigned Seat Numbers
    - Candidate Examination Rules & Instructions
    - Authentication Seals & Signature Placeholders
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    uni_name_style = ParagraphStyle(
        "UniName",
        parent=styles["Heading1"],
        fontSize=15,
        leading=18,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f172a"),
        alignment=1, # Centered
        spaceAfter=2
    )
    uni_sub_style = ParagraphStyle(
        "UniSub",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569"),
        alignment=1, # Centered
        spaceAfter=4
    )
    doc_title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontSize=12,
        leading=15,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1e3a8a"), # Navy
        alignment=1, # Centered
        spaceAfter=14
    )
    field_label_style = ParagraphStyle(
        "FieldLabel",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#334155")
    )
    field_val_style = ParagraphStyle(
        "FieldVal",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0f172a")
    )
    table_header_style = ParagraphStyle(
        "TblHdr",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f172a")
    )
    table_cell_style = ParagraphStyle(
        "TblCell",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1e293b")
    )
    seat_badge_style = ParagraphStyle(
        "SeatBadge",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1d4ed8")
    )
    instruction_style = ParagraphStyle(
        "Instruction",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#334155")
    )

    elements = []

    # 1. Header Banner
    elements.append(Paragraph("NATIONAL INSTITUTE OF HIGHER EDUCATION & RESEARCH", uni_name_style))
    elements.append(Paragraph("OFFICE OF THE REGISTRAR & CONTROLLER OF EXAMINATIONS", uni_sub_style))
    elements.append(Paragraph("OFFICIAL STUDENT ADMIT CARD / EXAMINATION HALL TICKET", doc_title_style))

    # 2. Candidate Profile Table
    s_id = student_data.get("student_id", "-")
    s_name = student_data.get("name", "-")
    s_dept = student_data.get("department", "-")
    s_sem = student_data.get("semester", "-")
    accommodations = student_data.get("special_accommodations", [])
    acc_text = ", ".join(accommodations) if accommodations else "Standard Seating (None Required)"

    profile_data = [
        [
            Paragraph("<b>Candidate Full Name:</b>", field_label_style),
            Paragraph(f"<b>{s_name}</b>", field_val_style),
            Paragraph("<b>Student / Roll ID:</b>", field_label_style),
            Paragraph(f"<b>{s_id}</b>", field_val_style),
        ],
        [
            Paragraph("<b>Academic Department:</b>", field_label_style),
            Paragraph(s_dept, field_val_style),
            Paragraph("<b>Academic Semester:</b>", field_label_style),
            Paragraph(str(s_sem), field_val_style),
        ],
        [
            Paragraph("<b>Accommodations:</b>", field_label_style),
            Paragraph(acc_text, field_val_style),
            Paragraph("<b>Timetable Version:</b>", field_label_style),
            Paragraph(timetable_name, field_val_style),
        ],
        [
            Paragraph("<b>Examination Term:</b>", field_label_style),
            Paragraph("Fall Semester 2026", field_val_style),
            Paragraph("<b>Status:</b>", field_label_style),
            Paragraph("<font color='#16a34a'><b>ACTIVE & ELIGIBLE</b></font>", field_val_style),
        ]
    ]

    profile_table = Table(profile_data, colWidths=[120, 160, 110, 142])
    profile_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(profile_table)
    elements.append(Spacer(1, 14))

    # 3. Examination Schedule Header
    sec_title = ParagraphStyle(
        "SecTitle",
        parent=styles["Heading2"],
        fontSize=10,
        leading=13,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6
    )
    elements.append(Paragraph(f"SCHEDULED COURSE EXAMINATIONS ({len(exams_seatings)} SUBJECTS ALLOCATED)", sec_title))

    # 4. Examination Schedule Table
    exam_headers = ["#", "Date", "Day", "Time Window", "Course Code", "Subject Name", "Exam Hall", "Building", "Allocated Seat"]
    table_rows = [[Paragraph(f"<b>{h}</b>", table_header_style) for h in exam_headers]]

    for idx, e in enumerate(exams_seatings):
        table_rows.append([
            Paragraph(str(idx + 1), table_cell_style),
            Paragraph(str(e.get("date", "-")), table_cell_style),
            Paragraph(e.get("day_name", "-"), table_cell_style),
            Paragraph(f"{e.get('start_time', '')} - {e.get('end_time', '')}", table_cell_style),
            Paragraph(e.get("course_code", "-"), table_header_style),
            Paragraph(e.get("course_name", "-")[:26], table_cell_style),
            Paragraph(e.get("room_code", "TBA"), table_header_style),
            Paragraph(e.get("building", "-")[:16], table_cell_style),
            Paragraph(e.get("seat_number", "Seat 01"), seat_badge_style),
        ])

    exam_table = Table(table_rows, colWidths=[20, 60, 52, 68, 62, 120, 50, 50, 50])
    exam_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    elements.append(exam_table)
    elements.append(Spacer(1, 14))

    # 5. Candidate Rules & Instructions
    elements.append(Paragraph("IMPORTANT CANDIDATE INSTRUCTIONS & DISCIPLINARY REGULATIONS", sec_title))
    instructions = [
        "1. <b>Admit Card & Identity Verification:</b> The candidate must present this official Admit Card along with their University Photo ID Card at the entrance of each examination hall. Candidates without valid identification will not be admitted.",
        "2. <b>Seating Allocation:</b> The candidate must occupy their designated desk number as printed above at least 15 minutes prior to the scheduled exam commencement time.",
        "3. <b>Prohibited Articles:</b> Mobile phones, programmable calculators, electronic storage media, smartwatches, and unauthorized written materials are strictly banned inside examination venues.",
        "4. <b>Hall Exit Protocol:</b> No candidate will be permitted to leave the examination hall during the first 60 minutes or the last 15 minutes of the allocated examination window.",
        "5. <b>Special Accommodations:</b> Candidates approved for accessibility or special accommodations must notify the Hall Superintendent upon entry for dedicated seating assistance."
    ]
    for inst in instructions:
        elements.append(Paragraph(inst, instruction_style))
        elements.append(Spacer(1, 3))

    elements.append(Spacer(1, 16))

    # 6. Signatures & Seals
    sign_data = [
        [
            Paragraph("<br/><br/>_____________________________________<br/><b>Candidate's Signature</b><br/>(To be signed in presence of Invigilator)", field_val_style),
            Paragraph("<br/><br/>_____________________________________<br/><b>Chief Hall Invigilator</b><br/>(Desk Verification & Attendance)", field_val_style),
            Paragraph("<br/><br/><b>Dr. R. K. Vance, Registrar</b><br/><b>Controller of Examinations</b><br/>National Examination Board", field_val_style),
        ]
    ]
    sign_table = Table(sign_data, colWidths=[180, 180, 172])
    sign_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
    ]))
    elements.append(sign_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def generate_backlogs_pdf(
    backlogs: List[Dict[str, Any]],
    department_filter: str = None
) -> bytes:
    """
    Generates official Department Backlog & Arrears Examination Schedule (Weekend Sessions).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=28,
        leftMargin=28,
        topMargin=28,
        bottomMargin=28
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "BkTitle",
        parent=styles["Heading1"],
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=2
    )
    sub_style = ParagraphStyle(
        "BkSub",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569"),
        spaceAfter=10
    )
    th_style = ParagraphStyle(
        "BkTh",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=9.5,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f172a")
    )
    td_style = ParagraphStyle(
        "BkTd",
        parent=styles["Normal"],
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#1e293b")
    )
    td_bold = ParagraphStyle(
        "BkTdBold",
        parent=styles["Normal"],
        fontSize=7,
        leading=9,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f172a")
    )
    badge_old = ParagraphStyle(
        "BkBadgeOld",
        parent=styles["Normal"],
        fontSize=6.5,
        leading=8,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#b45309")
    )

    elements = []

    # 1. Header
    dept_label = f"Department: {department_filter}" if department_filter and department_filter != "ALL" else "All Academic Departments"
    elements.append(Paragraph("<b>UNIVERSITY EXAMINATION REGISTRY • BACKLOG & ARREARS SCHEDULE</b>", title_style))
    elements.append(Paragraph(f"Special Saturday Examination Sessions (Sundays Off) • Fall 2026 Academic Term • {dept_label}", sub_style))

    # 2. Metric Summary
    total_bk = len(backlogs)
    odd_cnt = sum(1 for b in backlogs if "Odd" in b.get("semester_type", ""))
    sessions_cnt = len(set((b.get("exam_date"), b.get("period")) for b in backlogs if b.get("exam_date")))
    venues_cnt = len(set(b.get("room_code") for b in backlogs if b.get("room_code")))

    summary_data = [
        [
            Paragraph(f"<b>Total Backlog Candidates:</b> {total_bk}", td_style),
            Paragraph(f"<b>Odd Sem Arrears:</b> {odd_cnt}", td_style),
            Paragraph(f"<b>Saturday Exam Sessions:</b> {sessions_cnt}", td_style),
            Paragraph(f"<b>Allocated Exam Halls:</b> {venues_cnt}", td_style),
        ]
    ]
    summary_table = Table(summary_data, colWidths=[180, 180, 190, 190])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 10))

    # 3. Table Header (Old/New Student column removed from display)
    table_data = [
        [
            Paragraph("#", th_style),
            Paragraph("Candidate Details", th_style),
            Paragraph("Department", th_style),
            Paragraph("Current Sem", th_style),
            Paragraph("Backlog Sem", th_style),
            Paragraph("Backlog Subject & Course", th_style),
            Paragraph("Weekend Date & Day", th_style),
            Paragraph("Time Slot", th_style),
            Paragraph("Venue & Desk", th_style),
        ]
    ]

    for idx, b in enumerate(backlogs):
        row = [
            Paragraph(str(idx + 1), td_style),
            Paragraph(f"<b>{b.get('student_name', '')}</b><br/>{b.get('student_code', '')}", td_style),
            Paragraph(b.get("department", ""), td_style),
            Paragraph(b.get("current_semester", ""), td_style),
            Paragraph(f"<b>{b.get('backlog_semester', '')}</b><br/>({b.get('semester_type', '')})", td_style),
            Paragraph(f"<b>{b.get('course_code', '')}</b><br/>{b.get('course_name', '')}", td_style),
            Paragraph(f"<b>{b.get('exam_day', '')}</b><br/>{b.get('exam_date', '')}", td_bold),
            Paragraph(f"{b.get('start_time', '')[:5]} – {b.get('end_time', '')[:5]}<br/>({b.get('period', 'Morning')})", td_style),
            Paragraph(f"<b>{b.get('room_code', '')}</b><br/>Desk: <b>{b.get('seat_number', '')}</b>", td_bold),
        ]
        table_data.append(row)

    col_widths = [22, 118, 90, 60, 75, 145, 80, 75, 75]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def generate_backlog_admit_card_pdf(backlog: Dict[str, Any]) -> bytes:
    """
    Generates an official Individual Candidate Examination Admit Card / Hall Ticket
    specifically for a Backlog / Arrear candidate taking special weekend sessions.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    uni_name_style = ParagraphStyle(
        "UniName",
        parent=styles["Normal"],
        fontSize=13,
        leading=16,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f172a"),
        alignment=1,
        spaceAfter=2
    )
    uni_sub_style = ParagraphStyle(
        "UniSub",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceAfter=3
    )
    doc_title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#b45309"), # Amber/Gold institutional tone
        alignment=1,
        spaceAfter=12
    )
    field_label_style = ParagraphStyle(
        "FieldLabel",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#334155")
    )
    field_val_style = ParagraphStyle(
        "FieldVal",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0f172a")
    )
    th_style = ParagraphStyle(
        "AdmitTh",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=9.5,
        fontName="Helvetica-Bold",
        textColor=colors.white
    )
    td_style = ParagraphStyle(
        "AdmitTd",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1e293b")
    )
    td_bold = ParagraphStyle(
        "AdmitTdBold",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f172a")
    )
    seat_style = ParagraphStyle(
        "AdmitSeat",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1d4ed8")
    )
    instruction_style = ParagraphStyle(
        "AdmitInst",
        parent=styles["Normal"],
        fontSize=7,
        leading=9.5,
        textColor=colors.HexColor("#334155")
    )

    elements = []

    # 1. Header Banner
    elements.append(Paragraph("NATIONAL INSTITUTE OF HIGHER EDUCATION & RESEARCH", uni_name_style))
    elements.append(Paragraph("OFFICE OF THE CONTROLLER OF EXAMINATIONS • ACADEMIC REGISTRY", uni_sub_style))
    elements.append(Paragraph("OFFICIAL BACKLOG EXAMINATION ADMIT CARD / HALL TICKET", doc_title_style))

    # 2. Candidate Profile Table
    s_name = backlog.get("student_name", "-")
    s_code = backlog.get("student_code", "-")
    s_dept = backlog.get("department", "-")
    s_curr_sem = backlog.get("current_semester", "-")
    s_bk_sem = backlog.get("backlog_semester", "-")
    s_sem_type = backlog.get("semester_type", "Odd Semester")

    profile_data = [
        [
            Paragraph("<b>Candidate Name:</b>", field_label_style),
            Paragraph(f"<b>{s_name}</b>", field_val_style),
            Paragraph("<b>Student / Roll ID:</b>", field_label_style),
            Paragraph(f"<b>{s_code}</b>", field_val_style),
        ],
        [
            Paragraph("<b>Academic Department:</b>", field_label_style),
            Paragraph(s_dept, field_val_style),
            Paragraph("<b>Current Studying Sem:</b>", field_label_style),
            Paragraph(str(s_curr_sem), field_val_style),
        ],
        [
            Paragraph("<b>Arrear / Backlog Sem:</b>", field_label_style),
            Paragraph(f"{s_bk_sem} ({s_sem_type})", field_val_style),
            Paragraph("<b>Examination Window:</b>", field_label_style),
            Paragraph("Special Weekend Sessions (Sat/Sun)", field_val_style),
        ],
        [
            Paragraph("<b>Academic Term:</b>", field_label_style),
            Paragraph("Fall Semester 2026", field_val_style),
            Paragraph("<b>Eligibility Status:</b>", field_label_style),
            Paragraph("<font color='#16a34a'><b>APPROVED & SCHEDULED</b></font>", field_val_style),
        ]
    ]

    profile_table = Table(profile_data, colWidths=[120, 160, 115, 145])
    profile_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(profile_table)
    elements.append(Spacer(1, 12))

    # 3. Scheduled Examination Details
    sec_title = ParagraphStyle(
        "AdmitSecTitle",
        parent=styles["Heading2"],
        fontSize=9.5,
        leading=12,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=5
    )
    elements.append(Paragraph("SCHEDULED WEEKEND BACKLOG EXAMINATION PAPER", sec_title))

    exam_headers = ["Sl", "Course Code", "Course Title", "Exam Date", "Day", "Time Slot", "Examination Venue", "Allocated Desk"]
    exam_rows = [[Paragraph(f"<b>{h}</b>", th_style) for h in exam_headers]]

    exam_rows.append([
        Paragraph("1", td_style),
        Paragraph(backlog.get("course_code", "-"), td_bold),
        Paragraph(backlog.get("course_name", "-")[:34], td_style),
        Paragraph(str(backlog.get("exam_date", "-")), td_bold),
        Paragraph(str(backlog.get("exam_day", "-")), td_style),
        Paragraph(f"{backlog.get('start_time', '')[:5]} - {backlog.get('end_time', '')[:5]}", td_style),
        Paragraph(f"{backlog.get('room_name', backlog.get('room_code', 'TBA'))} ({backlog.get('room_code', '')})", td_bold),
        Paragraph(str(backlog.get("seat_number", "Allocated")), seat_style),
    ])

    exam_table = Table(exam_rows, colWidths=[20, 65, 145, 60, 50, 70, 75, 55])
    exam_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#ffffff")),
    ]))
    elements.append(exam_table)
    elements.append(Spacer(1, 14))

    # 4. Mandatory Instructions for Weekend Arrear Candidates
    elements.append(Paragraph("MANDATORY INSTRUCTIONS FOR ARREAR & BACKLOG CANDIDATES", sec_title))
    instructions = [
        "1. <b>Identity Verification:</b> Candidates must produce this official Admit Card along with their valid University Photo ID card.",
        "2. <b>Exam Timings:</b> Backlog re-examinations are conducted exclusively on Saturdays (Sundays are observed as holidays) to avoid conflict with standard weekday curriculum lectures.",
        "3. <b>Reporting Time:</b> Arrive at the examination hall at least 30 minutes prior to session start. No entry is permitted after 15 minutes from commencement.",
        "4. <b>Desk Allocation:</b> The candidate must occupy only the assigned desk indicated above. Any unauthorized seating change will result in disqualification.",
        "5. <b>Prohibited Items:</b> Mobile phones, smart devices, smartwatches, and programmable calculators are strictly prohibited in the exam hall.",
    ]
    for inst in instructions:
        elements.append(Paragraph(inst, instruction_style))
        elements.append(Spacer(1, 2))

    elements.append(Spacer(1, 18))

    # 5. Signatures Table
    sig_data = [
        [
            Paragraph("____________________________<br/><b>Candidate's Signature</b>", field_label_style),
            Paragraph("____________________________<br/><b>Hall Superintendent Seal</b>", field_label_style),
            Paragraph("<b>Digitally Approved</b><br/><b>Controller of Examinations</b>", field_label_style),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[180, 180, 180])
    sig_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(sig_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()



