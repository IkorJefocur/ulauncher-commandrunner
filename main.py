from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
import os
from logic import CommandList, Expression

class CommandRunner(Extension):

	def __init__(self, items_limit = 9):
		super().__init__()
		self.commands = CommandList()
		self.items_limit = items_limit

		self.subscribe(KeywordQueryEvent, KeywordQueryListener())
		self.subscribe(ItemEnterEvent, ItemEnterListener())

	def command_preference(self, name):
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
				env = Expression(extension.command_preference('terminal')).command
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

		expression = expression.wrap(extension.command_preference('shell'))
		if in_terminal:
			expression = expression.wrap(extension.command_preference('terminal'))

		expression.run()

if __name__ == '__main__':
	CommandRunner().run()