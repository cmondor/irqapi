from common.irq import *
from datetime import datetime
from flask_restful import Resource, reqparse, inputs, fields, marshal
import logging

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class InterruptAPIV1(object):
	def __init__(self, api=None):
		self.api = api
		self.attach_endpoints()

	def attach_endpoints(self):
		self.api.add_resource(InterruptDetailsAPI, '/irq/v1/interrupt_details')
		self.api.add_resource(PinIRQAPI,
			'/irq/v1/pin_irq')

class InterruptDetailsAPI(Resource):
	""" Flask-Restful endpoint for getting interrupt details. """

	def get(self):
		parser = reqparse.RequestParser(bundle_errors=True)
		parser.add_argument('begin_time', 
			type=self._get_datetime,
			required=True,
			help='bad begin_time, use %Y-%m-%dT%H:%M:%S')
		parser.add_argument('end_time',
			type=self._get_datetime,
			required=True,
			help='bad end_time, use %Y-%m-%dT%H:%M:%S')
		args = parser.parse_args()

		irq_details = IRQDetails(args.begin_time, args.end_time)
		balance_info = irq_details.get_balance_info()

		return marshal(balance_info, self.balanceinfo_fields, envelope='irq_details')

	def _get_datetime(self, value):
			return datetime.strptime(value,'%Y-%m-%dT%H:%M:%S')

	#output marshaling
	irqstat_fields = {
		'irq_num': fields.String,
		'irq_device': fields.String,
		'irq_type': fields.String,
		'cpu_interrupts': fields.List(fields.Integer),
		'cpu_interrupt_total': fields.Integer
	}

	cpu_fields = {
		'cpu': fields.String(attribute='cpu'),
		'interrupts': fields.Integer(attribute='count'),
		'percent': fields.Float(attribute='percent')	
	}

	balanceinfo_fields = { 
		'cpus': fields.List(fields.Nested(cpu_fields), attribute='cpus'),
		'irq_cpu_percent_distribution': fields.List(fields.Float,attribute='distribution'),
		'irq_cpu_count_distribution': fields.List(fields.Integer,attribute='counts'),
		'irq_distribution_metric': fields.Float(attribute='stdev'),
		'irq_stats': fields.List(fields.Nested(irqstat_fields),attribute='stats')
	}

class PinIRQAPI(Resource):
	""" Flask-Restful endpoint for pinning an IRQ Device to a CPU. """

	def post(self, irq_num=None, cpu=None):
		parser = reqparse.RequestParser(bundle_errors=True)
		parser.add_argument('irq_num', 
			type=int,
			required=True,
			help='irq_num must be an integer')
		parser.add_argument('cpu',
			type=int,
			required=True,
			help='cpu must be an integer')
		args = parser.parse_args()

		try:
			pin = PinIRQ(args.irq_num, args.cpu).pin_to_cpu()
		except Exception as e:
			return { 'message': "%s" % e}, 400

		return { 'OK': {'irq_num': args.irq_num,'cpu':args.cpu}}