import os
import re
import datetime
import sqlite3
from modules.config import Config, get_db
from flask import jsonify

def add_task(title, description, status='new', priority='medium'):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO tasks (title, description, status, priority)
                        VALUES (?, ?, ?, ?)''', (title, description, status, priority))
    conn.commit()
    conn.close()

def get_tasks():
    conn = get_db()  # Ensure this function returns a database connection
    cursor = conn.cursor()  # Create a cursor object using the connection
    
    try:
        cursor.execute('''
            SELECT 
                t.id,
                t.title,
                t.description,
                ts.id AS status_id,
                ts.status_name AS status,
                tp.id AS priority_id,
                tp.priority_name AS priority_name,
                tc.category_name AS category,
                t.assignee_id,
                a.name AS assignee_name,
                r.name AS reporter_id,
                t.due_date,
                t.attachment,
                t.resolution,
                t.created_at,
                t.updated_at
            FROM tasks t
            LEFT JOIN taskstatus ts ON t.status = ts.id
            LEFT JOIN taskpriority tp ON t.priority = tp.id
            LEFT JOIN taskcategory tc ON t.category = tc.id
            LEFT JOIN employees a ON t.assignee_id = a.id
            LEFT JOIN employees r ON t.reporter_id = r.id;
        ''')
        
        tasks = cursor.fetchall()
        # Convert the results into a list of dicts to jsonify
        tasks_list = [
            {
                'id': task['id'],
                'title': task['title'],
                'description': task['description'],
                'statusId': task['status_id'],
                'status': task['status'],
                'priorityId': task['priority_id'],
                'priority_name': task['priority_name'], 
                'category': task['category'],
                'assigneeId': task['assignee_id'], 
                'assignee_name': task['assignee_name'],
                'reporter_id': task['reporter_id'],
                'due_date': task['due_date'],
                'attachment': task['attachment'],
                'resolution': task['resolution'],
                'created_at': task['created_at'],
                'updated_at': task['updated_at']
            } for task in tasks
        ]
        
        return tasks_list
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        cursor.close()
        conn.close()

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


