import inspect
import asyncer
from linebot import WebhookHandler
from linebot.models.events import MessageEvent
from linebot.utils import LOGGER


class AsyncWebhookHandler(WebhookHandler):
    """Webhook Handler for asynchronous compatible

    Please read https://github.com/line/line-bot-sdk-python#webhookhandler
    """
    async def handle_async(self, body, signature):
        """Handle webhook.

        :param str body: Webhook request body (as text)
        :param str signature: X-Line-Signature value (as text)
        """
        payload = self.parser.parse(body, signature, as_payload=True)

        async with asyncer.create_task_group() as task_group:
            for event in payload.events:
                func = None
                key = None

                if isinstance(event, MessageEvent):
                    key = self.__get_handler_key(
                        event.__class__, event.message.__class__)
                    func = self._handlers.get(key, None)

                if func is None:
                    key = self.__get_handler_key(event.__class__)
                    func = self._handlers.get(key, None)

                if func is None:
                    func = self._default

                if func is None:
                    LOGGER.info('No handler of ' + key + ' and no default handler')
                else:
                    if inspect.iscoroutinefunction(func):
                        task_group.soonify(self.__invoke_func_async)(func, event, payload)
                    else:
                        self.__invoke_func(func, event, payload)


    @classmethod
    async def __invoke_func_async(cls, func, event, payload):
        ## START: copy from WebhookHandler.__invoke_func, but added function_return capture
        (has_varargs, args_count) = cls.__get_args_count(func)
        if has_varargs or args_count == 2:
            function_return = func(event, payload.destination)
        elif args_count == 1:
            function_return = func(event)
        else:
            function_return = func()
        ## END: copy from WebhookHandler.__invoke_func, but added function_return capture

        await function_return

