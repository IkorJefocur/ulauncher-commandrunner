import re
import itertools
import os
import subprocess

class CommandList:

	def __init__(self, folders = os.getenv('PATH').split(':')):
		folders = filter(lambda folder: os.access(folder, os.R_OK), folders)
		files = map(lambda folder: filter(
			lambda file: os.access(os.path.join(folder, file), os.X_OK)
		, os.listdir(folder)), folders)
		files = itertools.chain.from_iterable(files)
		self.items = set(files)

	def search(self, word):
		search_fn = lambda command: command.startswith(word)
		result = list(filter(search_fn, self.items))
		result.sort(key=lambda command: len(command))
		return result

class Expression:

	def __init__(self, data):
		self.data = data

	def __str__(self):
		return self.data

	@property
	def command(self):
		arg_break = self.data.find(' ')
		return self.data[: arg_break if arg_break != -1 else len(self.data)]

	@command.setter
	def command(self, value):
		self.data = self.data.replace(self.command, value, 1)

	def run(self):
		return subprocess.run(
			self.data,
			shell=True,
			cwd=os.getenv('HOME'),
			stdout=subprocess.PIPE,
			stdin=subprocess.PIPE,
			stderr=subprocess.PIPE
		)

	def wrap(self, wrapper, marker = '%'):
		quote_escape = lambda match: '\\' * ((len(match[1]) + 1) * 2 - 1) + '"'
		as_arg = '"' + re.sub(r'(\\*)"', quote_escape, self.data) + '"'

		inject = lambda match: as_arg if match[1] else self.data
		result = re.sub(rf'{marker}({marker})?', inject, str(wrapper))
		return type(self)(result)