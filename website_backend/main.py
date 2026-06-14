import sqlite3
import os
import smtplib
from email.message import EmailMessage
from fastapi.responses import StreamingResponse
import io
import csv
import secrets
from datetime import datetime
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

DB_PATH = "/home/marty/nexora/website_backend/early_access.db"
ADMIN_TOKEN = "nexora-admin-123"
SMTP_HOST = os.getenv("NEXORA_SMTP_HOST", "")
SMTP_PORT = int(os.getenv("NEXORA_SMTP_PORT", "587"))
SMTP_USER = os.getenv("NEXORA_SMTP_USER", "")
SMTP_PASSWORD = os.getenv("NEXORA_SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("NEXORA_SMTP_FROM", SMTP_USER)

app = FastAPI(title="Nexora Website Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EarlyAccessRequest(BaseModel):
    name: str
    email: EmailStr
    experience: str


class BetaApplicationRequest(BaseModel):
    name: str
    email: EmailStr
    experience: str
    trading_goal: str
    beta_reason: str



class AdminEmailRequest(BaseModel):
    subject: str
    message: str

class BetaStatusUpdateRequest(BaseModel):
    status: str
    admin_notes: str = ""

def send_email(to_email: str, subject: str, message: str):
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD or not SMTP_FROM:
        raise HTTPException(
            status_code=500,
            detail="Email system is not configured."
        )

    email = EmailMessage()
    email["From"] = SMTP_FROM
    email["To"] = to_email
    email["Subject"] = subject
    email.set_content(message)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(email)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS early_access (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            experience TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS beta_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            experience TEXT NOT NULL,
            trading_goal TEXT NOT NULL,
            beta_reason TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            admin_notes TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


@app.on_event("startup")
def startup():
    init_db()

@app.get("/public/feature-votes")
def get_feature_votes():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT feature, votes
        FROM feature_votes
        ORDER BY votes DESC, feature ASC
        """
    )

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "feature": row[0],
            "votes": row[1],
        }
        for row in rows
    ]


@app.post("/public/feature-votes/{feature}")
def vote_for_feature(feature: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE feature_votes
        SET votes = votes + 1
        WHERE feature = ?
        """,
        (feature,)
    )

    conn.commit()

    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Feature not found.")

    conn.close()

    return {
        "status": "success",
        "message": f"Vote added for {feature}."
    }

@app.get("/public/stats")
def public_stats():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM early_access")
    early_access_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM beta_applications")
    beta_application_count = cur.fetchone()[0]

    conn.close()

    return {
        "early_access_count": early_access_count,
        "beta_application_count": beta_application_count,
        "total_waitlist_count": early_access_count + beta_application_count,
    }

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS feature_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature TEXT NOT NULL UNIQUE,
            votes INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """

    )

    default_features = [
        "Coinbase Support",
        "Mobile App",
        "Advanced AI Signals",
        "Portfolio Analytics",
        "Strategy Builder",
    ]

    for feature in default_features:
        cur.execute(
            """

            INSERT OR IGNORE INTO feature_votes (feature, votes, created_at)
            VALUES (?, 0, ?)
            """,
            (feature, datetime.utcnow().isoformat()),
        )

@app.post("/early-access")
def save_early_access(data: EarlyAccessRequest):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO early_access (name, email, experience, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                data.name.strip(),
                data.email.strip().lower(),
                data.experience.strip(),
                datetime.utcnow().isoformat(),
            ),
        )

        conn.commit()

        return {
            "status": "success",
            "message": "You are on the Nexora early access list.",
        }

    except sqlite3.IntegrityError:
        return {
            "status": "exists",
            "message": "This email is already on the Nexora early access list.",
        }

    finally:
        conn.close()
@app.post("/beta-application")
def save_beta_application(data: BetaApplicationRequest):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO beta_applications (
                name,
                email,
                experience,
                trading_goal,
                beta_reason,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data.name.strip(),
                data.email.strip().lower(),
                data.experience.strip(),
                data.trading_goal.strip(),
                data.beta_reason.strip(),
                datetime.utcnow().isoformat(),
            ),
        )

        conn.commit()

        return {
            "status": "success",
            "message": "Your Nexora public beta application has been submitted.",
        }

    except sqlite3.IntegrityError:
        return {
            "status": "exists",
            "message": "This email has already submitted a public beta application.",
        }

    finally:
        conn.close()


@app.get("/admin/early-access")
def list_early_access(x_admin_token: str = Header(default="")):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, name, email, experience, created_at
        FROM early_access
        ORDER BY created_at DESC
        """
    )

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "experience": row[3],
            "created_at": row[4],
        }
        for row in rows
    ]

@app.patch("/admin/beta-applications/{application_id}/status")
def update_beta_application_status(
    application_id: int,
    data: BetaStatusUpdateRequest,
    x_admin_token: str = Header(default="")
):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    allowed_statuses = ["pending", "approved", "rejected"]

    if data.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid beta application status.")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE beta_applications
        SET status = ?, admin_notes = ?
        WHERE id = ?
        """,
        (
            data.status,
            data.admin_notes.strip(),
            application_id,
        ),
    )

    conn.commit()

    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Beta application not found.")

    conn.close()

    return {
        "status": "success",
        "message": f"Beta application marked as {data.status}."
    }

@app.get("/admin/beta-applications/metrics")
def beta_application_metrics(x_admin_token: str = Header(default="")):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM beta_applications")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM beta_applications WHERE status = 'pending'")
    pending = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM beta_applications WHERE status = 'approved'")
    approved = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM beta_applications WHERE status = 'rejected'")
    rejected = cur.fetchone()[0]

    conn.close()

    approval_rate = 0

    if total > 0:
        approval_rate = round((approved / total) * 100, 1)

    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "approval_rate": approval_rate
    }

@app.post("/admin/beta-applications/{application_id}/invite")
def generate_beta_invite(
    application_id: int,
    x_admin_token: str = Header(default="")
):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    invite_code = "NEX-BETA-" + secrets.token_hex(4).upper()
    invited_at = datetime.utcnow().isoformat()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE beta_applications
        SET invite_code = ?, invited_at = ?, status = 'approved'
        WHERE id = ?
        """,
        (
            invite_code,
            invited_at,
            application_id,
        ),
    )

    conn.commit()

    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Beta application not found.")

    conn.close()

    return {
        "status": "success",
        "message": "Beta invite generated.",
        "invite_code": invite_code,
        "invited_at": invited_at,
    }

@app.get("/admin/beta-applications")
def list_beta_applications(x_admin_token: str = Header(default="")):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, name, email, experience, trading_goal, beta_reason, created_at, status, admin_notes, invite_code, invited_at
        FROM beta_applications
        ORDER BY created_at DESC
        """
    )

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "experience": row[3],
            "trading_goal": row[4],
            "beta_reason": row[5],
            "created_at": row[6],
            "status": row[7],
            "admin_notes": row[8],
            "invite_code": row[9],
            "invited_at": row[10],
        }
        for row in rows
    ]


@app.get("/admin/early-access/export")
def export_early_access(x_admin_token: str = Header(default="")):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, name, email, experience, created_at
        FROM early_access
        ORDER BY created_at DESC
        """
    )

    rows = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["id", "name", "email", "experience", "created_at"])
    writer.writerows(rows)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=nexora_early_access.csv"
        },
    )

@app.post("/admin/email/early-access")
def email_early_access(
    data: AdminEmailRequest,
    x_admin_token: str = Header(default="")
):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT email FROM early_access")
    rows = cur.fetchall()
    conn.close()

    sent_count = 0

    for row in rows:
        send_email(row[0], data.subject.strip(), data.message.strip())
        sent_count += 1

    return {
        "status": "success",
        "message": f"Email sent to {sent_count} early access users."
    }


@app.post("/admin/email/beta-applications")
def email_beta_applications(
    data: AdminEmailRequest,
    x_admin_token: str = Header(default="")
):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT email FROM beta_applications")
    rows = cur.fetchall()
    conn.close()

    sent_count = 0

    for row in rows:
        send_email(row[0], data.subject.strip(), data.message.strip())
        sent_count += 1

    return {
        "status": "success",
        "message": f"Email sent to {sent_count} beta applicants."
    }

@app.get("/admin/beta-applications/export")
def export_beta_applications(x_admin_token: str = Header(default="")):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, name, email, experience, trading_goal, beta_reason, created_at
        FROM beta_applications
        ORDER BY created_at DESC
        """
    )

    rows = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "id",
        "name",
        "email",
        "experience",
        "trading_goal",
        "beta_reason",
        "created_at",
    ])

    writer.writerows(rows)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=nexora_beta_applications.csv"
        },
    )
