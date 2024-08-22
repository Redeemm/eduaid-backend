from flask import Flask, request, jsonify
import pandas as pd
import pickle
from flask_cors import CORS
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

pickle_file_path = "./hybrid_model.pkl"

with open(pickle_file_path, 'rb') as file:
    loaded_model = pickle.load(file)

app = Flask(__name__)
CORS(app)

def get_gpa_category(gpa_score):
    if 4.0 >= gpa_score >= 3.6:
        return 0
    elif 3.59 >= gpa_score >= 3.0:
        return 1
    elif 2.99 >= gpa_score >= 2.0:
        return 3
    else:
        return -1  # Return -1 for any GPA score outside the specified ranges

def get_message(prediction, gpa_score, internet_availability, study_mode):
    if prediction == 0:
        return f"Based on our analysis of your academic data, including your GPA score of {gpa_score}, which is considered good, along with the availability of Good internet network and your preference for a practical LMS mode, we believe there is a high probability of your success. With consistent dedication and hard work, you have the potential to achieve excellent results and even attain a first-class degree if you continue to study diligently. We encourage you to stay focused, remain motivated, and make the most out of your academic journey."
    elif prediction == 1:
        return f"Based on our analysis of your academic data, including your GPA score of {gpa_score}, which is considered good, along with the availability of {internet_availability} internet network and your preference for a practical {study_mode} mode, we believe there is a high probability of your success. With consistent dedication and hard work, you have the potential to achieve excellent results and even attain a second upper class degree if you continue to study diligently. We encourage you to stay focused, remain motivated, and make the most out of your academic journey."
    elif prediction == 2:
        return f"Based on our analysis of your academic data, including your GPA score of {gpa_score}, which is considered satisfactory for a second lower class, along with the availability of {internet_availability} internet network and your preference for a conventional {study_mode} mode, we believe there is a moderate probability of your success.With concerted effort and dedication, you have the potential to improve your academic standing and enhance your prospects for success. While achieving a first-class degree may be challenging, focusing on consistent improvement and making the most out of your academic journey will greatly contribute to your overall success. We encourage you to remain focused, stay motivated, and continue striving for excellence in your studies."
    elif prediction == 3:
        return f"Based on our analysis of your academic data, you have a low probability of success. Despite efforts, the student's GPA of {gpa_score} suggests challenges in academic performance. Coupled with {internet_availability} internet access and a passive {study_mode} study mode, the likelihood of achieving success is low. However, with personalized support, targeted interventions, and a commitment to academic improvement, the student can overcome obstacles and work towards enhancing their academic standing."
    elif prediction == 4:
        return f"Based on our analysis of your academic data, you have a very low probability of success: The student's GPA of {gpa_score} reflects significant academic struggles, indicating substantial room for improvement. Combined with {internet_availability} internet availability and a passive {study_mode} study mode, the likelihood of achieving success is very low. However, with dedicated support, tailored educational interventions, and a proactive approach to learning, the student can embark on a path towards academic improvement and strive to overcome existing challenges"
    else:
        return "Unknown prediction"

@app.route('/predict', methods=['POST'])
def multiPredict():
    try:
        if 'file' in request.files:
            file = request.files['file']
            # Check if the file has a permitted extension (Excel file)
            if file.filename.split('.')[-1] != 'xlsx':
                return jsonify({'error': 'Only Excel files (.xlsx) are allowed'}), 400

            # Read the Excel file
            df = pd.read_excel(file)
        else:
            # Check if the request contains JSON data
            if request.json is None:
                return jsonify({'error': 'No file or JSON data provided'}), 400

            # Load JSON data into a DataFrame
            df = pd.DataFrame(request.json)

        # Check if all required fields are present in the DataFrame
        required_fields = ['index', 'email', 'gender', 'level', 'gpa_score', 'class_mode', 'study_mode', 'internet_availability']
        if not all(field in df.columns for field in required_fields):
            return jsonify({'error': 'Missing required fields in data'}), 400

        # Convert 'gpa_score' column to float
        df['gpa_score'] = df['gpa_score'].astype(float)

        # Perform predictions
        prediction_list = []
        for _, row in df.iterrows():
            # Preprocess data if necessary and make predictions
            features = [[row['gender'], row['internet_availability'], row['study_mode'], get_gpa_category(row['gpa_score'])]]
            prediction = loaded_model.predict(features)
            message = get_message(prediction, row['gpa_score'], row['internet_availability'], row['study_mode'])
            prediction_dict = {
                'index': row['index'],
                'gender': row['gender'],
                'email': row['email'],
                'class_mode' : row['class_mode'],
                'level': row['level'],
                'internet_availability': row['internet_availability'],
                'study_mode': row['study_mode'],
                'gpa_score': row['gpa_score'],
                'prediction': int(prediction[0]),
                'message': message,
            }
            prediction_list.append(prediction_dict)


        return jsonify(prediction_list)

    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/predict/s', methods=['POST'])
def singlePredict():
    try:
        # Check if the request contains JSON data
        if request.json is None:
            return jsonify({'error': 'No JSON data provided'}), 400

        # Get JSON data from the request
        json_data = request.json

        # If the JSON data is not a list, wrap it in a list
        if not isinstance(json_data, list):
            json_data = [json_data]

        # Convert 'gpa_score' value to float
        for record in json_data:
            record['gpa_score'] = float(record['gpa_score'])

        # Perform predictions
        prediction_list = []
        for row in json_data:
            # Preprocess data if necessary and make predictions
            features = [[row['gender'], row['internet_availability'], row['study_mode'], get_gpa_category(row['gpa_score'])]]
            prediction = loaded_model.predict(features)
            message = get_message(prediction, row['gpa_score'], row['internet_availability'], row['study_mode'])
            prediction_dict = {
                'index': row.get('index', None),
                'gender': row.get('gender', None),
                'email': row.get('email', None),
                'class_mode' : row.get('class_mode', None),
                'level': row.get('level', None),
                'internet_availability': row.get('internet_availability', None),
                'study_mode': row.get('study_mode', None),
                'gpa_score': row.get('gpa_score', None),
                'prediction': int(prediction[0]),
                'message': message,
            }
            prediction_list.append(prediction_dict)

        return jsonify(prediction_list)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def send_email(receiver_email, message_content):
    # Email configuration
    sender_email = "redeemerdela419@gmail.com"  # Replace with your email address
    password = "ncxycyngzujaarsy"  # Replace with your email password
    smtp_server = "smtp.gmail.com"  # Replace with your SMTP server address
    smtp_port = 587  # Replace with your SMTP server port

    sender_name = "EduAid"

    # Create message container
    message = MIMEMultipart()
    message['From'] = f"{sender_name} <{sender_email}>"
    message['To'] = receiver_email
    message['Subject'] = "Student Academic Report"

    # Email content
    body = f"""
Dear Student,

{message_content}

Best regards,
EduAid Team
"""
    message.attach(MIMEText(body, 'plain'))

    # Establish SMTP connection
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, password)
        text = message.as_string()
        # Send email
        server.sendmail(sender_email, receiver_email, text)

    print("Email sent successfully!")

@app.route('/send-email', methods=['POST'])
def send_email_route():
    data = request.get_json()
    if 'email' in data and 'message' in data:
        email_address = data['email']
        message_content = data['message']
        send_email(email_address, message_content)
        return jsonify({'message': 'Email sent successfully'}), 200
    else:
        return jsonify({'error': 'Email address or message content not provided'}), 400



if __name__ == "__main__":
    app.run(debug=True, port=5001)
