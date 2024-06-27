from sqlalchemy.orm import sessionmaker

Session = sessionmaker(bind=engine)
session = Session()

# Create a new user
new_user = User(username='johndoe', email='john@example.com', password_hash='hashed_password')
session.add(new_user)
session.commit()

# Query the database
user = session.query(User).filter_by(username='johndoe').first()
print(user.email)
