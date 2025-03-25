from app import app, db
from sqlalchemy import text

if __name__ == '__main__':
    print("Initializing database...")
    
    with app.app_context():
        print("Disabling foreign key checks...")
        db.session.execute(text('SET FOREIGN_KEY_CHECKS = 0'))
        db.session.commit()
        
        try:
            print("Dropping existing tables...")
            tables = [
                'appointment',
                'date_specific_slot',
                'doctor_slot',
                'admitted_patient',
                'doctor',
                'patient'
            ]
            
            for table in tables:
                print(f"Dropping table {table}...")
                db.session.execute(text(f'DROP TABLE IF EXISTS {table}'))
            
            db.session.commit()
            
            print("Creating all tables...")
            db.create_all()
            
            # Initialize admin user and sample doctors
            from app import init_db
            init_db()
            
            print("Database initialized successfully!")
        finally:
            # Re-enable foreign key checks
            print("Re-enabling foreign key checks...")
            db.session.execute(text('SET FOREIGN_KEY_CHECKS = 1'))
            db.session.commit() 