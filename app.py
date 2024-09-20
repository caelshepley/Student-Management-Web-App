from json import dumps, loads
from bson import json_util
from flask import Flask, render_template, request, redirect, url_for, Response, jsonify
from collections import Counter
from datetime import datetime
import pymongo
import re
import os

app = Flask(__name__)
# to stop caching static file
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

MONGODB_URI='mongodb+srv://caelshepley23:rJ8y22a8s6v6ced4@30daysofpython.mjcor.mongodb.net/?retryWrites=true&w=majority&appName=30DaysOfPython'
client = pymongo.MongoClient(MONGODB_URI)
db = client['thirty_days_of_python'] # accessing the database
students_collection = db['students']  # Accessing the students collection

def get_most_frequent_word(text):
    # Remove punctuation and split text into words
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return None
    # Count frequency of each word
    word_counts = Counter(words)
    # Find the most common word
    most_common_word, _ = word_counts.most_common(1)[0]
    return most_common_word

def serialize_student(student):
    # Convert BSON date fields to string
    if 'dateofbirth' in student and isinstance(student['dateofbirth'], datetime):
        student['dateofbirth'] = student['dateofbirth'].strftime('%Y-%m-%d')
    if 'created_at' in student and isinstance(student['created_at'], datetime):
        student['created_at'] = student['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    return student

@app.route('/')  # this decorator create the home route
def home():
    front_end = ['HTML', 'CSS', 'JavaScript']
    back_end = ['Flask', 'MongoDB','Python']
    name = '30 Days Of Python Programming'
    return render_template('home.html', front_end=front_end, back_end=back_end, name=name, title='Home')

@app.route('/about')
def about():
    name = '30 Days Of Python Programming'
    return render_template('about.html', name=name, title='About Us')

@app.route('/result')
def result():
    # Retrieve the word count, character count, most frequent word, and content from the URL parameters
    word_count = request.args.get('word_count', 0)
    char_count = request.args.get('char_count', 0)
    most_frequent_word = request.args.get('most_frequent_word', 'N/A')
    content = request.args.get('content', '')
    return render_template('result.html', word_count=word_count, char_count=char_count,
                           most_frequent_word=most_frequent_word, content=content)

@app.route('/post', methods=['GET', 'POST'])
def post():
    name = 'Text Analyzer'
    if request.method == 'GET':
        return render_template('post.html', name=name, title=name)
    if request.method == 'POST':
        content = request.form['content']
        word_count = len(content.split())  # Calculate the number of words
        char_count = len(content)  # Calculate the number of characters
        most_frequent_word = get_most_frequent_word(content)  # Find the most frequent word
        return redirect(
            url_for('result', word_count=word_count, char_count=char_count,
                    most_frequent_word=most_frequent_word,content=content))

@app.route('/join', methods=['GET'])
def join():
    return render_template('join.html')

@app.route('/api/v1.0/students', methods=['GET'])
def students():
    students_data = list(students_collection.find({}, {'_id': 0}))
    students_data = [serialize_student(student) for student in students_data]
    return Response(dumps(students_data), mimetype='application/json')

@app.route('/api/v1.0/students', methods=['POST'])
def create_student():
    name = request.form['name']
    country = request.form['country']
    city = request.form['city']
    date_of_birth = request.form['dateofbirth']
    skills = request.form['skills'].split(', ')
    bio = request.form['bio']
    created_at = datetime.now()

    # Convert the dob string to a datetime object
    dob = datetime.strptime(date_of_birth, '%Y-%m-%d')

    student = {
        'name': name,
        'country': country,
        'city': city,
        'dateofbirth': dob,
        'skills': skills,
        'bio': bio,
        'created_at': created_at
    }

    db.students.insert_one(student)
    return redirect(url_for('list_students'))  # Redirect to the list of students or a success page

@app.route('/students')
def list_students():
    students_data = list(students_collection.find({}, {'_id': 0}))
    students_data = [serialize_student(student) for student in students_data]
    return render_template('students.html', students=students_data, title='Students')

@app.route('/delete_student/<string:name>', methods=['POST'])
def delete_student(name):
    # Remove student from the database
    result = students_collection.delete_one({'name': name})
    if result.deleted_count == 1:
        return redirect(url_for('list_students'))
    else:
        # Handle the case where the student was not found
        return "Student not found", 404

@app.route('/edit_student/<string:name>', methods=['GET'])
def edit_student(name):
    student = students_collection.find_one({'name': name}, {'_id': 0})
    if student:
        student = serialize_student(student)
        return render_template('edit_student.html', student=student)
    else:
        return "Student not found", 404

@app.route('/update_student/<string:name>', methods=['POST'])
def update_student(name):
    student = {
        'name': request.form['name'],
        'country': request.form['country'],
        'city': request.form['city'],
        'dateofbirth': datetime.strptime(request.form['dateofbirth'], '%Y-%m-%d'),
        'skills': request.form['skills'].split(', '),
        'bio': request.form['bio'],
        'created_at': datetime.now()  # Assuming you want to update the created_at field as well
    }

    result = students_collection.update_one({'name': name}, {'$set': student})
    if result.modified_count > 0:
        return redirect(url_for('list_students'))
    else:
        return "Failed to update student", 500

if __name__ == '__main__':
    # for deployment
    # to make it work for both production and development
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
