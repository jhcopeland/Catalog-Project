from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, CatUser, Category, CatItem

#engine = create_engine('sqlite:///usercategoryitem.db')
engine = create_engine('postgresql://catalog:sunshine25@localhost/usercategoryitem')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Create Categories
category1 = Category(name="Soccer")
session.add(category1)
session.commit()

category2 = Category(name="Basketball")
session.add(category2)
session.commit()

category3 = Category(name="Baseball")
session.add(category3)
session.commit()

category4 = Category(name="Frisbee")
session.add(category4)
session.commit()

category5 = Category(name="Snowboarding")
session.add(category5)
session.commit()

category6 = Category(name="Rock Climbing")
session.add(category6)
session.commit()

category7 = Category(name="Foosball")
session.add(category7)
session.commit()

category8 = Category(name="Skating")
session.add(category8)
session.commit()

category9 = Category(name="Hockey")
session.add(category9)
session.commit()

# Create default user
user1 = CatUser(name="Default User", email="default@email.com")
session.add(user1)
session.commit()

# Create items for default user
catItem1 = CatItem(user_id=1, name="Jersey", description="""100% polyester breathable and moisture whisking fabric.  Red with black stripes and the number 13 on the back.""", category=category1)
session.add(catItem1)
session.commit()

catItem2 = CatItem(user_id=1, name="Shorts", description="""100% polyester breathable and moisture whisking fabric.  All black and coming down to just 1 inch above the knee.""", category=category1)
session.add(catItem2)
session.commit()

catItem3 = CatItem(user_id=1, name="Shinguards", description="""Standard shinguards covering the area 1 inch above the ankle and extending to 2 inches below the knee.""", category=category1)
session.add(catItem3)
session.commit()

catItem4 = CatItem(user_id=1, name="Soccer Cleats", description="""100% synthetic leather with removable studs not exceeding 0.5 inches in length.""", category=category1)
session.add(catItem4)
session.commit()

print "Added default category items to database!"
