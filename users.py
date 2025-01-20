from flask import Flask, request, jsonify
import boto3
import json
import itertools

app = Flask(__name__)

# AWS SQS Configuration (Replace with your actual SQS URL)
SQS_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/831785949054/SubmissionQueue'

# AWS SQS client setup
sqs_client = boto3.client('sqs', region_name='us-east-1') 

# Weight coefficients
weight_time = 0.5  # wt
weight_expense = 0.5  # we

# Price vector and execution time matrixa
price_vector = [1, 1.2, 1.5, 1.8, 2]  # p
t_hat = [
    [6, 5, 4, 3.5, 3],
    [5, 4.2, 3.6, 3, 2.8],
    [4, 3.5, 3.2, 2.8, 2.4]
]

initial_vector = [0,0,0,0,0]
initial_util = 0

def calc_utilfunction(T, E):
    global weight_time
    global weight_expense

    max_execution_time = max(T)
    sum_costs = sum(E)

    return 1 / (weight_time * max_execution_time + weight_expense * sum_costs)

def setup_user(user_choice):
    global price_vector
    global t_hat

    # User-specific configurations
    user_configs = {
        1: {"userId": 1, "num_subtasks": 2, "max_time": 6, "max_expense": 6},
        2: {"userId": 2, "num_subtasks": 3, "max_time": 5, "max_expense": 5},
        3: {"userId": 3, "num_subtasks": 4, "max_time": 4, "max_expense": 4},
    }

    if user_choice not in user_configs:
        raise ValueError("Invalid user choice. Please enter 1, 2, or 3.")

    user_info = user_configs[user_choice]

    num_resources = len(price_vector)

    resource_combinations = list(itertools.product([0, 1], repeat=num_resources))
    
    valid_combinations = [combo for combo in resource_combinations if sum(combo) == user_info["num_subtasks"]]

    optimal_utility = float('-inf')
    allocVector = [0, 0, 0, 0, 0]

    for assignment in valid_combinations:
        selected_execution_times = [t_hat[user_info["userId"] - 1][i] for i in range(num_resources) if assignment[i] == 1]
        selected_costs = [t_hat[user_info["userId"] - 1][i] * price_vector[i] for i in range(num_resources) if assignment[i] == 1]

        max_execution_time = max(selected_execution_times)
        sum_costs = sum(selected_costs)

        print(f"Trying: {assignment}, Execution Time: {max_execution_time}, Sum of Expense: {sum_costs}, Expense: {0.5 * max_execution_time + 0.5 * sum_costs}")

        if max_execution_time <= user_info["max_time"] and (0.5 * max_execution_time + 0.5 * sum_costs) <= user_info["max_expense"]:
            utility = calc_utilfunction(selected_execution_times, selected_costs)

            if utility > optimal_utility:
                optimal_utility = utility
                allocVector = assignment

    user = {
        "userId": user_info["userId"],
        "num_subtasks": user_info["num_subtasks"],
        "max_time": user_info["max_time"],
        "max_expense": user_info["max_expense"],
        "initial_util": optimal_utility,
        "allocVector": allocVector,
    }

    return user

@app.route('/receive', methods=['POST'])
def receive_matrix():
    try:
        data = request.get_json()
        user_id = data.get('userId')
        T = data.get('T')
        E = data.get('E')

        if not user_id or not T or not E:
            return jsonify({'message': 'Invalid input, userId or resultMatrix missing'}), 400

        calculated_utility = calc_utilfunction(T, E)
        print(f"Received matrix for user {user_id} with calculated utility: {calculated_utility}")


        return jsonify({'message': 'Matrix received successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def send_to_sqs(user):
    try:        
        user_id = user['userId']
        alloc_vector = user['allocVector']

        if not user_id or not alloc_vector:
            print('Invalid input, userId or allocVector missing')
            return

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

    except Exception as e:
        print(f"Error sending message to SQS: {str(e)}")


user_input = int(input("Enter user choice (1, 2, or 3): "))
user_data = setup_user(user_input)

print(user_data)

send_to_sqs(user_data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
