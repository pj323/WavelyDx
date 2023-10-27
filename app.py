from flask import Flask, render_template, request, redirect, url_for, abort
import boto3
import os
import uuid
import random
from pydub import AudioSegment

app = Flask(__name__)

# AWS S3 Configuration
S3_BUCKET = 'wavelydx'
S3_ACCESS_KEY = 'AKIARGOGFJTRXIGQ5KVV'
S3_SECRET_KEY = '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'
S3_REGION = 'us-east-2'

s3 = boto3.client(
    's3',
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name=S3_REGION
)

# Function to upload audio to S3
def upload_to_s3(file, bucket_name, s3_client):
    file_name = str(uuid.uuid4()) + '.mp3'  # Generating a unique filename
    s3_client.upload_file(file, bucket_name, file_name)
    return file_name

# Function to retrieve audio from S3
def get_from_s3(file_name, bucket_name, s3_client):
    local_file_path = f'tmp/{file_name}'
    s3_client.download_file(bucket_name, file_name, local_file_path)
    return local_file_path


# Function to get the list of uploaded files with their last modified time
def get_uploaded_files(bucket_name, s3_client):
    response = s3_client.list_objects(Bucket=bucket_name)
    files = response.get('Contents', [])
    return sorted(files, key=lambda x: x['LastModified'], reverse=True)


# Mock Mood Detection (replace this with your actual implementation)
def detect_mood():
    # Your mood detection logic goes here
    # For now, returning a random mood
    moods = ['Happy', 'Sad', 'Calm']
    return random.choice(moods)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        return redirect(request.url)

    if file:
        # Ensure the 'tmp' directory exists
        os.makedirs('tmp', exist_ok=True)

        # Save the uploaded file locally
        file_path = os.path.join('tmp', file.filename)
        file.save(file_path)

        # Upload the file to S3
        s3_file_name = upload_to_s3(file_path, S3_BUCKET, s3)

        # Delete the local file
        os.remove(file_path)

        return redirect(url_for('index'))

@app.route('/retrieve_mood')
def retrieve_mood():
    # Get the list of uploaded files with their last modified time
    files = get_uploaded_files(S3_BUCKET, s3)

    if not files:
        return "No files available."

    # Get the most recently uploaded file
    latest_file = files[0]['Key']

    # Retrieve the file from S3
    local_file_path = get_from_s3(latest_file, S3_BUCKET, s3)

    # Perform mood detection (replace this with your actual implementation)
    mood = detect_mood()

    return f"Latest Mood detected for '{latest_file}': {mood}"


if __name__ == '__main__':
    app.run(debug=True)
