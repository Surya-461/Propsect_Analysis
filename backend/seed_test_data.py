"""Script to insert sample test data into the database"""
from database import SessionLocal
from models import ProspectAnalysisDB
import datetime

db = SessionLocal()

# Sample test data
test_companies = [
    {
        "company_name": "Acme Insurance Corp",
        "executive_summary": "Leading provider of commercial insurance solutions with strong market presence in the Northeast region.",
        "report_data": {
            "Market Position": {"summary": "Strong regional presence", "key_facts": ["#1 in Northeast"], "sources": []},
            "Financial Health": {"summary": "Stable revenue growth", "key_facts": ["10% YoY growth"], "sources": []}
        }
    },
    {
        "company_name": "Global Risk Solutions Inc",
        "executive_summary": "International risk management firm serving enterprise clients across multiple industries.",
        "report_data": {
            "Global Reach": {"summary": "Operating in 45 countries", "key_facts": ["Multi-national operations"], "sources": []},
            "Client Base": {"summary": "Fortune 500 companies", "key_facts": ["Enterprise focus"], "sources": []}
        }
    },
    {
        "company_name": "TechCare Underwriting",
        "executive_summary": "Specialized in cyber and tech insurance with innovative digital platforms.",
        "report_data": {
            "Technology": {"summary": "AI-powered underwriting", "key_facts": ["Digital-first platform"], "sources": []},
            "Specialization": {"summary": "Cyber insurance leader", "key_facts": ["Cyber focused"], "sources": []}
        }
    },
    {
        "company_name": "Healthcare Coverage Partners",
        "executive_summary": "Focused on health and wellness insurance products for mid-market organizations.",
        "report_data": {
            "Market Segment": {"summary": "Mid-market focus", "key_facts": ["Healthcare segment"], "sources": []},
            "Product Portfolio": {"summary": "Comprehensive health plans", "key_facts": ["Multiple product lines"], "sources": []}
        }
    }
]

# Check if data already exists
existing_count = db.query(ProspectAnalysisDB).count()
print(f"Existing records: {existing_count}")

if existing_count == 0:
    # Insert test data
    for i, company in enumerate(test_companies):
        # Stagger creation dates
        created_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=3-i)
        
        analysis = ProspectAnalysisDB(
            company_name=company["company_name"],
            executive_summary=company["executive_summary"],
            report_data=company["report_data"],
            created_at=created_at
        )
        db.add(analysis)
    
    db.commit()
    print(f"✓ Inserted {len(test_companies)} test records into database")
    
    # Verify insertion
    records = db.query(ProspectAnalysisDB).all()
    print(f"✓ Total records now: {len(records)}")
    for record in records:
        print(f"  - {record.id}: {record.company_name} (created: {record.created_at.strftime('%Y-%m-%d %H:%M:%S')})")
else:
    print(f"✓ Database already has {existing_count} records")
    records = db.query(ProspectAnalysisDB).order_by(ProspectAnalysisDB.created_at.desc()).all()
    for record in records:
        print(f"  - {record.id}: {record.company_name} (created: {record.created_at.strftime('%Y-%m-%d %H:%M:%S')})")

db.close()
