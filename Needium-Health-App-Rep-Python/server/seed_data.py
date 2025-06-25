from sqlalchemy.orm import Session
from models import Doctor, Pharmacy
from database import SessionLocal, engine, create_tables

def seed_database():
    """Seed the database with sample data"""
    create_tables()
    
    db = SessionLocal()
    try:
        # Check if data already exists
        existing_doctors = db.query(Doctor).count()
        existing_pharmacies = db.query(Pharmacy).count()
        
        if existing_doctors == 0:
            # Seed sample doctors
            sample_doctors = [
                Doctor(
                    first_name="Sarah",
                    last_name="Wilson",
                    specialty="Cardiology",
                    email="s.wilson@hospital.com",
                    phone="(555) 123-4567",
                    address="123 Medical Center Dr",
                    city="Healthcare City",
                    state="HC",
                    zip_code="12345",
                    consultation_fee=200.00,
                    rating=4.9,
                    review_count=127,
                    availability=["today", "tomorrow"],
                    image_url="https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?ixlib=rb-4.0.3&w=100&h=100&fit=crop&crop=face"
                ),
                Doctor(
                    first_name="Michael",
                    last_name="Chen",
                    specialty="Family Medicine",
                    email="m.chen@clinic.com",
                    phone="(555) 234-5678",
                    address="456 Riverside Ave",
                    city="Healthcare City",
                    state="HC",
                    zip_code="12345",
                    consultation_fee=150.00,
                    rating=4.7,
                    review_count=89,
                    availability=["tomorrow", "this_week"],
                    image_url="https://images.unsplash.com/photo-1582750433449-648ed127bb54?ixlib=rb-4.0.3&w=100&h=100&fit=crop&crop=face"
                ),
                Doctor(
                    first_name="Emily",
                    last_name="Rodriguez",
                    specialty="Pediatrics",
                    email="e.rodriguez@children.com",
                    phone="(555) 345-6789",
                    address="789 Children's Way",
                    city="Healthcare City",
                    state="HC",
                    zip_code="12345",
                    consultation_fee=180.00,
                    rating=5.0,
                    review_count=156,
                    availability=["this_week"],
                    image_url="https://images.unsplash.com/photo-1559839734-2b71ea197ec2?ixlib=rb-4.0.3&w=100&h=100&fit=crop&crop=face"
                )
            ]
            
            for doctor in sample_doctors:
                db.add(doctor)

        if existing_pharmacies == 0:
            # Seed sample pharmacies
            sample_pharmacies = [
                Pharmacy(
                    name="CVS Pharmacy",
                    address="123 Main Street",
                    city="Healthcare City",
                    state="HC",
                    zip_code="12345",
                    phone="(555) 123-4567",
                    hours="Open until 10 PM",
                    distance=0.8
                ),
                Pharmacy(
                    name="Walgreens",
                    address="456 Oak Avenue",
                    city="Healthcare City",
                    state="HC",
                    zip_code="12345",
                    phone="(555) 234-5678",
                    hours="Open 24 hours",
                    distance=1.2
                )
            ]
            
            for pharmacy in sample_pharmacies:
                db.add(pharmacy)
                
        db.commit()
        print("Database seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()