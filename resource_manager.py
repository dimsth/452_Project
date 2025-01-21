from flask import Flask, request, jsonify
import json
import http.client

app = Flask(__name__)

price_vector = [1, 1.2, 1.5, 1.8, 2] 
t_hat = [
    [6, 5, 4, 3.5, 3],
    [5, 4.2, 3.6, 3, 2.8],
    [4, 3.5, 3.2, 2.8, 2.4]
]

# EC2 instances to send results to (replace with actual EC2 private/public IPs)
EC2_INSTANCES = [
    ("34.227.107.136", 5000),  # Tuple of (IP, port)
    ("34.228.75.119", 5000),
    ("100.26.51.7", 5000)
]

allocator_matrix = {
    1: [0] * len(t_hat[0]),
    2: [0] * len(t_hat[0]),
    3: [0] * len(t_hat[0])
}

@app.route('/process', methods=['POST'])
def process_request():
    try:
        data = request.get_json()

        allocator_matrix[1] = list(map(int, data.get('allocVector0', [])))
        allocator_matrix[2] = list(map(int, data.get('allocVector1', [])))
        allocator_matrix[3] = list(map(int, data.get('allocVector2', [])))

        T, E = compute_T_and_E(allocator_matrix)
        
        send_results_to_ec2(T, E)

        return jsonify({'message': 'Matrix processed and sent to EC2 instances', 'T': T[user_id - 1], 'E': E[user_id - 1]})


    except Exception as e:
        return jsonify({'error': str(e)}), 500


def compute_T_and_E(allocMatrix):

    T = [[0] * len(t_hat[0]) for _ in range(3)]
    E = [[0] * len(t_hat[0]) for _ in range(3)]

    column_totals = [sum(allocMatrix[user][j] for user in allocMatrix) for j in range(len(t_hat[0]))]

    for user_id, allocation in allocMatrix.items():
        for j in range(len(t_hat[0])):
            if allocation[j] == 1:
                T[user_id - 1][j] = t_hat[user_id - 1][j] * column_totals[j]
                E[user_id - 1][j] = t_hat[user_id - 1][j] * price_vector[j]

    return T, E

def send_results_to_ec2(T, E):

    for index, (ec2_ip, ec2_port) in enumerate(EC2_INSTANCES, start=1):
        try:
            payload = json.dumps({
                'userId': index,
                'T': T[index - 1],
                'E': E[index - 1]
            })

            print(payload)

            conn = http.client.HTTPConnection(ec2_ip, ec2_port)
            headers = {'Content-Type': 'application/json'}

            conn.request("POST", "/receive", body=payload, headers=headers)

            response = conn.getresponse()
            response_data = response.read().decode('utf-8')

            print(f"Sent results for user {index} to {ec2_ip}:{ec2_port}, Response: {response.status}, {response_data}")
            conn.close()

        except Exception as e:
            print(f"Error sending to {ec2_ip}:{ec2_port} - {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
