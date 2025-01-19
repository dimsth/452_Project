from flask import Flask, request, jsonify
import boto3
import json

app = Flask(__name__)

# AWS SQS Configuration (Replace with your actual SQS URL)
SQS_QUEUE_URL = 'https://sqs.YOUR_REGION.amazonaws.com/YOUR_ACCOUNT_ID/YOUR_QUEUE_NAME'

# AWS SQS client setup
sqs_client = boto3.client('sqs')

def setup_user(user_choice):
    weight_time = 0.5  # wt
    weight_expense = 0.5  # we
    price_vector = [1, 1.2, 1.5, 1.8, 2]  # p
    execution_time_matrix = [
        [6, 5, 4, 3.5, 3], 
        [5, 4.2, 3.6, 3, 2.8], 
        [4, 3.5, 3.2, 2.8, 2.4]
    ]  # t_hat

    # User-specific configurations
    user_configs = {
        1: {"userId": 1, "num_subtasks": 2, "max_time": 6, "max_expense": 6},
        2: {"userId": 2, "num_subtasks": 3, "max_time": 5, "max_expense": 5},
        3: {"userId": 3, "num_subtasks": 4, "max_time": 4, "max_expense": 4},
    }

    if user_choice not in user_configs:
        raise ValueError("Invalid user choice. Please enter 1, 2, or 3.")

    user_info = user_configs[user_choice]

    user = {
        "userId": user_info["userId"],
        "num_subtasks": user_info["num_subtasks"],
        "max_time": user_info["max_time"],
        "max_expense": user_info["max_expense"],
        "weight_time": weight_time,
        "weight_expense": weight_expense,
        "price_vector": price_vector,
        "execution_time_matrix": execution_time_matrix
    }

    return user

@app.route('/receive', methods=['POST'])
def receive_matrix():
    """ Receive the matrix from the resource manager """
    try:
        data = request.get_json()
        user_id = data.get('userId')
        result_matrix = data.get('resultMatrix')

        if not user_id or not result_matrix:
            return jsonify({'message': 'Invalid input, userId or resultMatrix missing'}), 400

        print(f"Received matrix for user {user_id}: {result_matrix}")

        return jsonify({'message': 'Matrix received successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/send-to-sqs', methods=['POST'])
def send_to_sqs():
    """ Send userId and allocVector to SQS queue """
    try:
        data = request.get_json()
        
        user_id = data.get('userId')
        alloc_vector = data.get('allocVector')

        if not user_id or not alloc_vector:
            return jsonify({'message': 'Invalid input, userId or allocVector missing'}), 400

        message_body = {
            'userId': user_id,
            'allocVector': alloc_vector
        }

        # Send message to SQS queue
        response = sqs_client.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(message_body)
        )

        print(f"Sent to SQS: {response['MessageId']}")

        return jsonify({'message': 'Data sent to SQS successfully', 'messageId': response['MessageId']}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    try:
        user_input = int(input("Enter user choice (1, 2, or 3): "))
        user_data = setup_user(user_input)
        print("User data initialized:", user_data)

        # Start the Flask server after setting up the user
        app.run(host='0.0.0.0', port=5000, debug=True)

    except ValueError as e:
        print("Error:", e)
