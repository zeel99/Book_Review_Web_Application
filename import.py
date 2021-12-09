import csv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def main():
    f = open("books.csv")
    reader = csv.reader(f)

    for isbn, title, author, year in reader:
        db.execute(
            "INSERT INTO books (num, title, author, year) VALUES(:num, :title,:author,:year)",
            {"num": isbn, "title": title, "author": author, "year": year}
        )

        print(f"The book {title} has been added to Database.")
        db.commit()


if __name__ == "__main__":
    main()
