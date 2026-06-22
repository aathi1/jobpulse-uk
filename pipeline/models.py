from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(100), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    company = Column(String(255))
    location = Column(String(255))
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    description = Column(Text)
    url = Column(String(500))
    source = Column(String(50))
    date_posted = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Job {self.title} at {self.company}>"


class Insight(Base):
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    insight_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Insight {self.insight_type} at {self.created_at}>"
