import csv
import psycopg2

conn = psycopg2.connect(
    host="ep-soft-silence-alvyints-pooler.c-3.eu-central-1.aws.neon.tech",
    dbname="neondb",
    user="neondb_owner",
    password="npg_8sMOZ7hqxaYe",
    sslmode="require"
)
cur = conn.cursor()

with open("raw_articles.csv", "r", encoding="utf-8") as f:
    # COPY est le plus rapide
    cur.copy_expert("COPY raw_articles FROM STDIN WITH CSV HEADER", f)

conn.commit()
cur.execute("SELECT COUNT(*) FROM raw_articles")
print(f"Lignes importees sur Neon : {cur.fetchone()[0]}")
cur.close()
conn.close()
