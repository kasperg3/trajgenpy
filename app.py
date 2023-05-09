import scikit_build_example._core as planner
from flask import Flask, jsonify

planner.add(1,2)

# app = Flask(__name__)

# @app.route('/example', methods=['post'])
# def example():
#     return jsonify({'result': 'success'})  # Return a JSON response

# if __name__ == '__main__':
#     app.run(debug=True, host="0.0.0.0", port=5000)