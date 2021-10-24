from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
import itertools
import shlex
import os
import subprocess

class CommandRunner(Extension):

	def __init__(self, items_limit = 9):
		super().__init__()
		self.commands = CommandList()
		self.items_limit = items_limit

		self.subscribe(KeywordQueryEvent, KeywordQueryListener())
		self.subscribe(ItemEnterEvent, ItemEnterListener())

class KeywordQueryListener(EventListener):

	def on_event(self, event, extension):
		query = event.get_argument()
		if not query:
			return DoNothingAction()

		result = []
		in_terminal = event.get_keyword() == extension.preferences['keyword_terminal']
		query = shlex.split(query)
		commands = extension.commands.search(query[0])[:extension.items_limit]
		args = query[1:]
		argsDescription = shlex.join(args)

		for command in commands:
			description = f'Run command "{command}"'
			data = [command, *args]

			if in_terminal:
				terminal = shlex.split(os.path.expandvars(extension.preferences['terminal']))
				description = f'Launch "{terminal[0]}" with command "{command}"'
				data = [*terminal, '--', *data]

			result.append(ExtensionResultItem(
				icon='images/icon.svg',
				name=f'{command} {argsDescription}',
				description=description,
				on_enter=ExtensionCustomAction(data)
			))

		return RenderResultListAction(result)

class ItemEnterListener(EventListener):

	def on_event(self, event, extension):
		command = event.get_data()
		subprocess.run(
			command,
			stdout=subprocess.PIPE,
			stdin=subprocess.PIPE,
			stderr=subprocess.PIPE
		)

class CommandList:

	def __init__(self, folders = os.getenv('PATH').split(':')):
		folders = filter(lambda folder: os.access(folder, os.R_OK), folders)
		files = map(lambda folder: filter(
			lambda file: os.access(os.path.join(folder, file), os.X_OK)
		, os.listdir(folder)), folders)
		files = itertools.chain.from_iterable(files)
		self.items = set(files)

	def search(self, word):
		result = list(filter(lambda command: command.startswith(word), self.items))
		result.sort(key=lambda command: len(command))
		return result

if __name__ == '__main__':
	CommandRunner().run()