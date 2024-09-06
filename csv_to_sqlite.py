import csv
import sqlite3


def csv_to_sqlite(csv_file, db_file, table_names):
    target_header = "Registration No."

    # Connect to SQLite database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Read the CSV file
    with open(csv_file, "r") as file:
        csv_reader = csv.reader(file)
        headers = next(csv_reader)

        header_index = headers.index(target_header)

        # Create table
        for table_name in table_names:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            cursor.execute(
                f"CREATE TABLE {table_name} (\n"
                "registration_number CHAR(9) PRIMARY KEY,\n"
                "is_scanned BOOLEAN DEFAULT FALSE,\n"
                "last_scanned DATETIME);"
            )

        # Insert data
        for row in csv_reader:
            reg_no = row[header_index]
            for table_name in table_names:
                try:
                    cursor.execute(
                        f"INSERT INTO {table_name} (registration_number) VALUES ('{reg_no}')"
                    )
                except sqlite3.IntegrityError as e:
                    print(f"Got {e} due to {reg_no}, continuing")

    conn.commit()
    conn.close()

    print(
        f"Data from {csv_file} has been successfully imported to {db_file} in tables {table_names}."
    )


if __name__ == "__main__":
    db_file = "registrations.db"

    csv_file = "registered.csv"
    table_names = ["wristband", "culturals", "concert", "sadhya"]

    csv_to_sqlite(csv_file, db_file, table_names)
