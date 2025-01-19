from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

# Placeholder for execution time matrix (t_hat)
t_hat = [
    [6, 5, 4, 3.5, 3], 
    [5, 4.2, 3.6, 3, 2.8], 
    [4, 3.5, 3.2, 2.8, 2.4]
]

# EC2 instances to send results to (replace with actual EC2 private/public IPs)
EC2_INSTANCES = [
    "http://ec2-instance-1-ip:5000/receive",
    "http://ec2-instance-2-ip:5000/receive",
    "http://ec2-instance-3-ip:5000/receive"
]

@app.route('/process', methods=['POST'])
def process_request():
    try:
        data = request.get_json()

        user_id = data.get('userId')
        alloc_vector = data.get('allocVector')

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


def send_results_to_ec2(user_id, matrix):
    headers = {'Content-Type': 'application/json'}
    payload = {
        'userId': user_id,
        'resultMatrix': matrix
    }

    for ec2_url in EC2_INSTANCES:
        try:
            response = requests.post(ec2_url, data=json.dumps(payload), headers=headers)
            if response.status_code == 200:
                print(f"Successfully sent matrix to {ec2_url}")
            else:
                print(f"Failed to send matrix to {ec2_url}, status code: {response.status_code}")
        except Exception as e:
            print(f"Error sending to {ec2_url}: {e}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
