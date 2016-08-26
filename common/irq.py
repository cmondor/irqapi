import copy
import operator
import os
import re
import statistics as s
import sys
import logging

log = logging.getLogger(__name__)

class PinIRQ(object):
	def __init__(self, irq_num=None, cpu=None):
		self.irq_num = irq_num
		self.cpu = cpu

	def pin_to_cpu(self):
		if not os.path.exists('/proc/irq/%d' % self.irq_num):
			raise IRQNotFoundException
		if self._get_cpu_count() - 1 < self.cpu:
			raise CPUNotFoundException

		if not os.path.exists('/proc/irq/%d/smp_affinity' % self.irq_num):
			try:
				pass
				# commented out for demo purposes
				# irq_affinity_file = open('/proc/irq/%d/smp_affinity' % self.irq_num, '+w')
				# irq_affinity_file.write(cpu + 1)
				# irq_affinity_file.close()
			except IOError as e:
				raise PinException

	def _get_cpu_count(self):
		cpu_count = 0
		try:
			interrupt_file = open('/proc/interrupts')
			first_line = interrupt_file.readline().count('CPU')
			interrupt_file.close()
			cpu_count = first_line
		except IOError:
			raise IOError
		return cpu_count


class PinException(Exception):
	def __init__(self):
		Exception.__init__(self, "Unable to Pin Exception")

class CPUNotFoundException(Exception):
	def __init__(self):
		Exception.__init__(self, "CPU not found Exception.")

class IRQNotFoundException(Exception):
	def __init__(self):
		Exception.__init__(self, "IRQ not found Exception.")


class IRQDetails(object):
	""" Determining whether interrupts are balanced and suggest fixes. """

	def __init__(self, begin_time=None, end_time=None, interrupts_file=None):
		self.interrupts_file = interrupts_file if interrupts_file else 'proc_interrupts.txt'
		self.cpu_count = 0
		self.irq_stats = []
		self.begin_time = begin_time
		self.end_time = end_time
		self.default_balance_algo = AlternatingBalanceAlgo
		self._populate_irq_stats()

	def get_stats(self):
		return self.irq_stats

	def get_balance_info(self):
		return BalanceAlgo(self.irq_stats).get_balance_info()

	def get_balanced_info(self, balanceAlgo=None):
		balanceAlgo = self.default_balance_algo if balanceAlgo is None else balanceAlgo
		algo = balanceAlgo(self.irq_stats)
		return algo.get_balance_info()

	def print_irq_stats(self, stats=None):
		if stats is None:
			stats = self.irq_stats
		for irq_stat in stats:
			pass
			# print irq_stat

	def _populate_irq_stats(self):
		""" Parse interrupts_file and populate self.irq_stats with IRQStat objects. """
		try:
			interrupt_file = open(self.interrupts_file)
		except IOError:
			raise IOError

		first_line = True
		for line in interrupt_file:
			if first_line:
				first_line = False
				continue
			irq_stat = IRQStat().parse_line(line)
			if irq_stat.irq_device is None:
				# print "**WARNING** Unable to parse line: %s skipping" % line
				continue
			my_cpu_count = len(irq_stat.cpu_interrupts)
			self.cpu_count = my_cpu_count if my_cpu_count > self.cpu_count else self.cpu_count
			self.irq_stats.append(irq_stat)
		interrupt_file.close()

class IRQStat(object):
	"""Interrupt details and counts object."""

	def __init__(self):
		self.irq_num = None,
		self.irq_type = None, 
		self.irq_device = None,
		self.cpu_interrupts = [],
		self.cpu_interrupt_total = 0

	def parse_line(self, line):
		return self._parse_interrupt_line(line)

	def _parse_interrupt_line(self, line):
		match = re.match('^\s?(\w*):\s*([0-9]*)\s*([0-9]*)\s*([\w-]*)\s*([\w-]*)', line)
		if match and len(match.groups()) > 3:
			if re.match('^[a-zA-Z]', match.group(1)):
				return self
			self.irq_num = int(match.group(1))
			self.irq_device = match.groups()[-1]
			self.irq_type = match.groups()[-2]
			self.cpu_interrupts = [int(i) for i in match.groups()[1:-2]]
			self.cpu_interrupt_total = sum(self.cpu_interrupts)
		return self


class BalanceInfo(object):
	def __init__(self, stats=None,instructions=None,distribution=None,counts=None,stdev=None):
		self.stats = stats
		self.instructions = instructions
		self.distribution = distribution
		self.counts = counts
		self.stdev = stdev
		self.cpus = []

		log.info(counts)
		log.info(distribution)

		i = 0
		for count in counts:
			log.info(counts[i])
			log.info(distribution[i])
			self.cpus.append({'cpu': "CPU%d" % i,
				'count': counts[i],
				'percent': distribution[i]})
			i += 1

class BalanceAlgo(object):

	def __init__(self, irq_stats=None):
		self.irq_stats_balanced       = []
		self.irq_balance_instructions = []
		self.irq_distribution         = []
		self.irq_counts               = []
		self.stdev                    = -1
		self.cpu_count                = 0
		self.irq_stats = [] if irq_stats is None else irq_stats 

		if len(irq_stats) > 0:
			self.cpu_count = len(irq_stats[0].cpu_interrupts)

	def get_balance_info(self):
		self.balance_stats()
		(self.irq_counts, self.irq_distribution) = self.get_irq_distribution()
		if len(self.irq_distribution) > 0:
			self.stdev = s.stdev(self.irq_distribution)

		balance_info = BalanceInfo(stats=self.irq_stats_balanced,
			instructions=self.irq_balance_instructions,
			distribution=self.irq_distribution,
			counts=self.irq_counts,
			stdev=self.stdev)

		return balance_info

	def balance_stats(self):
		self.irq_stats_balanced = self.irq_stats

	def get_irq_distribution(self, stats=None):
		cpu_sums = []
		cpu_percentages = []
		if stats is None:
			stats = self.irq_stats_balanced
		for irq_stat in stats:
			cpu_interrupts = irq_stat.cpu_interrupts
			if len(cpu_sums) < 1:
				cpu_sums = [0,] * self.cpu_count
			i=0
			for cpu_interrupt_cnt in cpu_interrupts:
				cpu_sums[i] += cpu_interrupt_cnt
				i+=1
		total_interrupts = sum(cpu_sums)
		j=0
		cpu_percentages = [0,] * self.cpu_count
		for cpu_sum in cpu_sums:
			cpu_percentages[j] = (cpu_sum / float(total_interrupts)) * 100
			j+=1
		return (cpu_sums, cpu_percentages)

	def _sort_balanced_stats(self):
		self.irq_stats_balanced.sort(key=operator.itemgetter('irq_num'))

class AlternatingBalanceAlgo(BalanceAlgo):
	def balance_stats(self):
		cpu_interrupt_accum = [0,] * self.cpu_count
		i=0
		for irq_stat in self.irq_stats:
			least_interrupts_index = i
			cpu_interrupt_accum[least_interrupts_index] += irq_stat.cpu_interrupt_total
			self.irq_balance_instructions.append("pin %s to CPU%d" % (irq_stat.irq_num,
				least_interrupts_index))
			balanced_irq_stat = copy.deepcopy(irq_stat)

			for num in range(self.cpu_count):
				if num is not i:
					balanced_irq_stat.cpu_interrupts[num] = 0
				else:
					balanced_irq_stat.cpu_interrupts[num] = irq_stat.cpu_interrupt_total
			self.irq_stats_balanced.append(balanced_irq_stat)
			i = i + 1 if i + 1 != self.cpu_count else 0
		self.irq_balance_instructions.sort()
		self._sort_balanced_stats()
		return self.irq_stats_balanced


class LeastUsedBalanceAlgo(BalanceAlgo):
	def balance_stats(self):
		return self._least_used_balance()

	def _least_used_balance(self, stats=None):
		stats = self.irq_stats if stats is None else stats
		cpu_interrupt_accum = [0,] * self.cpu_count
		for irq_stat in stats:
			least_interrupts_index = cpu_interrupt_accum.index(min(cpu_interrupt_accum))
			cpu_interrupt_accum[least_interrupts_index] += irq_stat.cpu_interrupt_total
			self.irq_balance_instructions.append("pin %s to CPU%d" % (irq_stat.irq_num,
				least_interrupts_index))
			balanced_irq_stat = copy.deepcopy(irq_stat)

			for num in range(self.cpu_count):
				if num is not least_interrupts_index:
					balanced_irq_stat.cpu_interrupts[num] = 0
				else:
					balanced_irq_stat.cpu_interrupts[num] = irq_stat.cpu_interrupt_total
			self.irq_stats_balanced.append(balanced_irq_stat)
		self.irq_balance_instructions.sort()
		self._sort_balanced_stats()
		return self.irq_stats_balanced		


class SortedLeastUsedBalanceAlgo(LeastUsedBalanceAlgo):
	def balance_stats(self):
		return self._least_used_balance(self._sort_stats())

	def _sort_stats(self):
		sorted_irq_stats = copy.deepcopy(self.irq_stats)
		sorted_irq_stats.sort(key=operator.itemgetter('cpu_interrupt_total'))
		return sorted_irq_stats

class ReverseSortedLeastUsedBalanceAlgo(LeastUsedBalanceAlgo):

	def balance_stats(self):
		return self._least_used_balance(self._sort_stats())

	def _sort_stats(self):
		sorted_irq_stats = copy.deepcopy(self.irq_stats)
		sorted_irq_stats.sort(key=operator.itemgetter('cpu_interrupt_total'), reverse=True)
		return sorted_irq_stats