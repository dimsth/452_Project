from flask import Flask, request, jsonify
import requests
import json
import socket
import http.client

app = Flask(__name__)

# Placeholder for execution time matrix (t_hat)
t_hat = [
    [6, 5, 4, 3.5, 3],
    [5, 4.2, 3.6, 3, 2.8],
    [4, 3.5, 3.2, 2.8, 2.4]
]

# EC2 instances to send results to (replace with actual EC2 private/public IPs)
EC2_INSTANCES = [
    ("ec2-instance-2-ip", 5000),  # Tuple of (IP, port)
    # ("ec2-instance-2-ip", 5000),
    # ("ec2-instance-3-ip", 5000)
]

@app.route('/process', methods=['POST'])
def process_request():
    try:
        data = request.get_json()

        user_id = int(data.get('userId'))
        alloc_vector = list(map(int, data.get('allocVector', [])))

        if not user_id or not alloc_vector:
            return jsonify({'message': 'Invalid input, userId or allocVector missing'}), 400

        print(f"Received data for user {user_id}: {alloc_vector}")

        # For now, use the predefined t_hat matrix
        result_matrix = t_hat

        # Send the matrix to the three EC2 instances
        send_results_to_ec2(user_id, result_matrix)

        return jsonify({'message': 'Matrix processed and sent to EC2 instances', 'result': result_matrix})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def send_results_to_ec2(user_id, result_matrix):
    """ Send the corresponding row from t_hat to external EC2 instances via HTTP POST """

    if user_id not in [1, 2, 3]:
        print("Invalid user ID. Must be 1, 2, or 3.")
        return

    matrix_row = result_matrix[user_id - 1]

    payload = json.dumps({
        'userId': user_id,
        'resultMatrix': matrix_row
    })

    for ec2_ip, ec2_port in EC2_INSTANCES:
        try:
            # Create HTTP connection to EC2 instance
            conn = http.client.HTTPConnection(ec2_ip, ec2_port)
            headers = {'Content-Type': 'application/json'}

            # Correctly formatted HTTP POST request with version
            conn.request("POST", "/receive", body=payload, headers=headers)

            response = conn.getresponse()
            response_data = response.read().decode('utf-8')

            print(f"Sent matrix row for user {user_id} to {ec2_ip}:{ec2_port}, Response: {response.status}, {response_data}")
            conn.close()

        except Exception as e:
            print(f"Error sending to {ec2_ip}:{ec2_port} - {e}")



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
