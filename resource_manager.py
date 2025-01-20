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
    # ("ec2-instance-1-ip", 5000),
    # ("ec2-instance-2-ip", 5000),
    # ("ec2-instance-3-ip", 5000)
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

        allocator_matrix = [list(map(int, data.get('allocVector0', []))),
        list(map(int, data.get('allocVector1', []))),
        list(map(int, data.get('allocVector2', [])))]

        if all(sum(allocator_matrix[u]) > 0 for u in allocator_matrix):
            T, E = compute_T_and_E()

            send_results_to_ec2(user_id, T[user_id - 1], E[user_id - 1])

            return jsonify({'message': 'Matrix processed and sent to EC2 instances', 'T': T[user_id - 1], 'E': E[user_id - 1]})
        else:
            return jsonify({'message': 'Waiting for all users to send allocation vectors'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def compute_T_and_E():

    T = [[0] * len(t_hat[0]) for _ in range(3)]
    E = [[0] * len(t_hat[0]) for _ in range(3)]

    column_totals = [sum(allocator_matrix[user][j] for user in allocator_matrix) for j in range(len(t_hat[0]))]

    for user_id, allocation in allocator_matrix.items():
        for j in range(len(t_hat[0])):
            if allocation[j] == 1:
                T[user_id - 1][j] = t_hat[user_id - 1][j]

                if column_totals[j] > 0:
                    E[user_id - 1][j] = t_hat[user_id - 1][j] * (price_vector[j] / column_totals[j])

    return T, E

def send_results_to_ec2(user_id, T_row, E_row):

    payload = json.dumps({
        'userId': user_id,
        'T': T_row,
        'E': E_row
    })

    for ec2_ip, ec2_port in EC2_INSTANCES:
        try:
            conn = http.client.HTTPConnection(ec2_ip, ec2_port)
            headers = {'Content-Type': 'application/json'}

            conn.request("POST", "/receive", body=payload, headers=headers)

            response = conn.getresponse()
            response_data = response.read().decode('utf-8')

            print(f"Sent results for user {user_id} to {ec2_ip}:{ec2_port}, Response: {response.status}, {response_data}")
            conn.close()

        except Exception as e:
            print(f"Error sending to {ec2_ip}:{ec2_port} - {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
