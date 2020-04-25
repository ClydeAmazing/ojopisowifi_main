from django import template
from datetime import timedelta
import math

register = template.Library()

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

	time = ''
	if days > 0:
		time += '{} day '.format(str(days))

	if hours > 0:
		time += '{} hr '.format(str(hours))

	if minutes > 0:
		time += '{} min '.format(str(minutes))

	if seconds > 0:
		time += '{} sec'.format(str(seconds))

	return time