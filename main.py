from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
import re
import itertools
import os
import subprocess

class CommandRunner(Extension):

	def __init__(self, items_limit = 9):
		super().__init__()
		self.commands = CommandList()
		self.items_limit = items_limit

		self.subscribe(KeywordQueryEvent, KeywordQueryListener())
		self.subscribe(ItemEnterEvent, ItemEnterListener())

	def command_param(self, name):
		return os.path.expandvars(self.preferences[name])

	def in_terminal(self, keyword):
		return self.preferences['keyword_terminal'] == keyword

class KeywordQueryListener(EventListener):

	def on_event(self, event, extension):
		query = event.get_argument()
		if not query:
			return DoNothingAction()
		query = Expression(query)

		in_terminal = extension.in_terminal(event.get_keyword())
		commands = extension.commands.search(query.command)
		commands = commands[:extension.items_limit]
		result = []

		for variant in commands:
			expression = Expression(query.data)
			expression.command = variant
			description = f'Run command "{variant}"'

			if in_terminal:
				env = Expression(extension.command_param('terminal')).command
				description = f'Launch "{env}" with command "{variant}"'

			result.append(ExtensionResultItem(
				icon='images/icon.svg',
				name=str(expression),
				description=description,
				on_enter=ExtensionCustomAction([expression, in_terminal])
			))

		return RenderResultListAction(result)

class ItemEnterListener(EventListener):

	def on_event(self, event, extension):
		expression, in_terminal = event.get_data()

		if in_terminal:
			expression = expression.wrap(extension.command_param('terminal'))
		expression = expression.wrap(extension.command_param('shell'))

		expression.run()

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

if __name__ == '__main__':
	CommandRunner().run()