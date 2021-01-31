import ast

import telebot

from src.bot.deadline import Deadline, DEADLINE_PRIORITY_MAP
from src.bot.service import Service, ApiException
from src.bot.event_manager import event_manager, Event, EventType


class InlineKeyboardManager:
    def __init__(self, bot: telebot.TeleBot, service: Service):
        self.bot = bot
        self.service = service
        self.keyboard_commands = {
            # пользователь захотел изменить приоритет дедлайна
            'edit_deadline_priority': self._edit_deadline_priority,

            'edit_deadline_description': self._edit_deadline_description,

            # пользователь выбрал конкретное значение приоритета
            'set_deadline_priority': self._set_deadline_priority,

            # задать markup с главным меню
            'deadline_menu': self._deadline_menu,

            # удалить дедлайн и сообщение с ним
            'remove_deadline': self._remove_deadline,

            # получить сообщение с информацией о дедлайне для управления им
            'about_deadline': self._about_deadline,

            # позволяет из группового чата добавить дедлайн в свой список дедлайнов
            'import_deadline': self._import_deadline
        }

    @staticmethod
    def get_markup_for_deadline(d: Deadline, is_group=False) -> telebot.types.InlineKeyboardMarkup:
        markup = telebot.types.InlineKeyboardMarkup()
        if d.leadTime:
            markup.add(telebot.types.InlineKeyboardButton(
                text='Изменить приоритет',
                callback_data=str({
                    'action': 'edit_deadline_priority',
                    'id': d.id
                })
            ))
        markup.add(telebot.types.InlineKeyboardButton(
            text=('добавить' if not d.description else 'изменить') + ' описание',
            callback_data=str({
                'action': 'edit_deadline_description',
                'id': d.id
            })
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            text='удалить',
            callback_data=str({
                'action': 'remove_deadline',
                'id': d.id
            })
        ))
        if is_group:
            markup.add(telebot.types.InlineKeyboardButton(
                text='Импортировать',
                callback_data=str({
                    'action': 'import_deadline',
                    'id': d.id
                })
            ))

        return markup

    def _import_deadline(self, q: telebot.types.CallbackQuery, data: dict):
        d = self.service.get_deadline(data['id'])
        d.groupId = q.from_user.id
        d = self.service.post_deadline(d)
        self.bot.send_message(q.from_user.id, f'импортирован дедлайн:\n{d.to_string(False)}',
                              reply_markup=self.get_markup_for_deadline(d, False))

    def _edit_deadline_description(self, q: telebot.types.CallbackQuery, data: dict):
        def description_handler(message: telebot.types.Message):
            if not message.text:
                self.bot.send_message(message.chat.id, 'ошибка!')
                return
            d = self.service.patch_deadline(data['id'], {'description': message.text})
            self.bot.edit_message_text(d.to_string(False), message.chat.id, q.message.message_id,
                                       reply_markup=self.get_markup_for_deadline(d, q.message.chat.type == 'group'))

        self.bot.send_message(q.message.chat.id, "Отправь мне новое описание")
        self.bot.register_next_step_handler_by_chat_id(q.message.chat.id, description_handler)

    def _deadline_menu(self, q: telebot.types.CallbackQuery, data: dict):
        deadline = self.service.get_deadline(data['id'])
        self.bot.edit_message_reply_markup(q.message.chat.id, q.message.message_id, q.inline_message_id,
                                           self.get_markup_for_deadline(deadline, q.message.chat.type == 'group'))

    def _edit_deadline_priority(self, q: telebot.types.CallbackQuery, data: dict):
        deadline = self.service.get_deadline(data['id'])
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(
            text='Назад',
            callback_data=str({
                'action': 'deadline_menu',
                'id': data['id']
            })
        ))
        for k, v in DEADLINE_PRIORITY_MAP.items():
            if k != deadline.priority:
                markup.add(telebot.types.InlineKeyboardButton(
                    text=v,
                    callback_data=str({
                        'action': 'set_deadline_priority',
                        'value': k,
                        'id': data['id']
                    })
                ))
        self.bot.edit_message_reply_markup(q.message.chat.id, q.message.message_id, q.inline_message_id, markup)

    def _set_deadline_priority(self, q: telebot.types.CallbackQuery, data: dict):
        deadline = self.service.patch_deadline(data['id'], {'priority': data['value']})
        self.bot.edit_message_text(deadline.to_string(), q.message.chat.id, q.message.message_id)
        self.bot.edit_message_reply_markup(q.message.chat.id, q.message.message_id, q.inline_message_id,
                                           self.get_markup_for_deadline(deadline))
        event_manager.emit(Event(EventType.SCHEDULE_CHANGING_CHECK, message=q.message))

    def _remove_deadline(self, q: telebot.types.CallbackQuery, data: dict):
        self.service.delete_deadline(data['id'], q.message.chat.id)
        self.bot.answer_callback_query(q.id, 'Дедлайн удалён!', show_alert=True)
        self.bot.delete_message(q.message.chat.id, q.message.message_id)
        event_manager.emit(Event(EventType.SCHEDULE_CHANGING_CHECK, message=q.message))

    @staticmethod
    def get_markup_for_deadlines(deadlines: list[Deadline]) -> telebot.types.InlineKeyboardMarkup:
        markup = telebot.types.InlineKeyboardMarkup()
        for it in deadlines:
            markup.add(telebot.types.InlineKeyboardButton(
                text=it.id,
                callback_data=str({
                    'action': 'about_deadline',
                    'id': it.id
                })
            ))
        return markup

    def _about_deadline(self, q: telebot.types.CallbackQuery, data: dict):
        try:
            deadline = self.service.get_deadline(data['id'])
            self.bot.send_message(q.message.chat.id, deadline.to_string(short=False),
                                  reply_markup=self.get_markup_for_deadline(deadline, q.message.chat.type == 'group'))
        except ApiException as e:
            if e.code == 404:
                self.bot.answer_callback_query(q.id, 'Дедлайн не найден!', show_alert=True)
            else:
                raise

    def handle_query(self, q: telebot.types.CallbackQuery):
        data = ast.literal_eval(q.data)
        self.keyboard_commands[data['action']](q, data)
