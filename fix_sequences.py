from app.db.database import engine
import sqlalchemy as sa

with engine.connect() as conn:
    conn.execute(sa.text("SELECT setval('job_descriptions_id_seq', (SELECT MAX(id) FROM job_descriptions))"))
    conn.execute(sa.text("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))"))
    conn.commit()
    print("Sequences reset successfully")