from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView
from server.bre import bre
import base64

bre_blueprint = Blueprint('bre_apis', __name__)

class BreApis(MethodView):
    """
    APIs for business rules extraction
    """
    def post(self):
        try:
            post_data = request.get_json()
            rule_desc_b64 = post_data.get('rule_desc')
            rule_desc = base64.b64decode(rule_desc_b64)
            print('rule desc is ', rule_desc)
            rule_repr = bre.run_one_rule(rule_desc.decode('utf-8'))
            responseObject = {
                'status': 'success',
                'message': rule_repr
            }
            return make_response(jsonify(responseObject)), 200
        except Exception as e:
            print(e)
            responseObject = {
                'status': 'fail',
                'message': 'something wrong in bre service ...'
            }
            return make_response(jsonify(responseObject)), 500
    

# define the API resources

bre_view = BreApis.as_view('bre_apis')

# add Rules for API Endpoints
bre_blueprint.add_url_rule(
    '/bre',
    view_func=bre_view,
    methods=['POST']
)