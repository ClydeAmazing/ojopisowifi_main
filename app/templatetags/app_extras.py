from django import template
from datetime import timedelta
import math

register = template.Library()

def pluralize(number, hand):
	if number == 1:
		return str(number) + " " + hand + " "
	elif number > 1:
		return str(number) + " " + hand + "s "
	else:
		return ""

@register.filter
def duration(td):
	if not td:
		total_seconds = 0
	else:
		if isinstance(td, timedelta):
			total_seconds = int(td.total_seconds())
		else:
			total_seconds = td

	days = math.floor(total_seconds / 86400)
	hours = math.floor((total_seconds % 86400) / 3600)
	minutes = math.floor((total_seconds % 3600) / 60)
	seconds = math.floor((total_seconds % 60))

	time = pluralize(days, 'day')
	time += pluralize(hours, 'hr')
	time += pluralize(minutes, 'min')
	time += pluralize(seconds, 'sec')

	return time