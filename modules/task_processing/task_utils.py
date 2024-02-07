import os
import re
import datetime
import sqlite3
from modules.config import Config, get_db

def add_task(title, description, status='new', priority='medium'):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO tasks (title, description, status, priority)
                        VALUES (?, ?, ?, ?)''', (title, description, status, priority))
    conn.commit()
    conn.close()

def get_tasks():
    conn = get_db()
    cursor = conn.cursor()
    # Adjust the query below as necessary based on your database schema
    cursor.execute('''SELECT tasks.*, employees.name AS assignee_name 
                      FROM tasks
                      LEFT JOIN employees ON tasks.assignee_id = employees.id
                      ORDER BY tasks.created_at DESC''')
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def get_comments_for_task(task_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM comments WHERE task_id = ? ORDER BY created_at DESC', (task_id,))
    comments = cursor.fetchall()
    conn.close()
    return comments

def add_comment_to_task(task_id, commenter_name, comment):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO comments (task_id, commenter_name, comment) VALUES (?, ?, ?)',
                   (task_id, commenter_name, comment))
    conn.commit()
    conn.close()


