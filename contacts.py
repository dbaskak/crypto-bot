import psycopg2


def connect_db():
    return psycopg2.connect(
        dbname="contacts",
        user="db_admin",
        password="1111111",
        host="localhost"
    )


def add_contact(name, phone, email, conn):
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO contacts (name, phone, email) VALUES (%s, %s, %s)",
                       (name, phone, email))
        conn.commit()


def get_contacts(conn):
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name, phone, email FROM contacts")
        return cursor.fetchall()


def delete_contact(contact_id, conn):
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM contacts WHERE id = %s", (contact_id,))
        conn.commit()