from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os
import time
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'controller-db'),
        database=os.environ.get('DB_NAME', 'bytebrew_logs'),
        user=os.environ.get('DB_USER', 'admin'),
        password=os.environ.get('DB_PASSWORD', 'password')
    )
    return conn

# Initialize DB
def init_db():
    retries = 5
    while retries > 0:
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id SERIAL PRIMARY KEY,
                    type VARCHAR(50),
                    source_ip VARCHAR(50),
                    username VARCHAR(100),
                    password VARCHAR(100),
                    timestamp DOUBLE PRECISION,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            cur.close()
            conn.close()
            logger.info("Database initialized successfully.")
            break
        except Exception as e:
            logger.error(f"Database connection failed: {e}. Retrying...")
            retries -= 1
            time.sleep(5)

@app.route('/api/logs', methods=['POST'])
def receive_log():
    data = request.json
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO logs (type, source_ip, username, password, timestamp) VALUES (%s, %s, %s, %s, %s)",
            (data.get('type'), data.get('source_ip'), data.get('username'), data.get('password'), data.get('timestamp'))
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "success"}), 201
    except Exception as e:
        logger.error(f"Error saving log: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT type, source_ip, username, password, timestamp, created_at FROM logs ORDER BY created_at DESC LIMIT 50")
        rows = cur.fetchall()
        logs = []
        for row in rows:
            logs.append({
                "type": row[0],
                "source_ip": row[1],
                "username": row[2],
                "password": row[3],
                "timestamp": row[4],
                "created_at": row[5]
            })
        cur.close()
        conn.close()
        return jsonify(logs)
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Total attacks
        cur.execute("SELECT COUNT(*) FROM logs")
        total_attacks = cur.fetchone()[0]
        
        # Unique attackers
        cur.execute("SELECT COUNT(DISTINCT source_ip) FROM logs")
        unique_attackers = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        return jsonify({
            "total_attacks": total_attacks,
            "unique_attackers": unique_attackers
        })
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Wait for DB to start
    time.sleep(5)
    init_db()
    app.run(host='0.0.0.0', port=5000)
