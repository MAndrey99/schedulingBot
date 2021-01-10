from src.bot.deadline import Deadline


class Schedule:
    __slots__ = ('scheduledDeadlines', 'unscheduledDeadlines')
    
    @staticmethod
    def from_dict(data: dict) -> 'Schedule':
        res = Schedule()
        res.scheduledDeadlines = \
            [Deadline.from_dict(it) for it in data['scheduledDeadlines']] \
            if data['scheduledDeadlines'] is not None \
            else []
        res.unscheduledDeadlines = \
            [Deadline.from_dict(it) for it in data['unscheduledDeadlines']] \
            if data['unscheduledDeadlines'] is not None \
            else []
        return res
    
    def to_string(self) -> str:
        if self.scheduledDeadlines:
            user_message = [
                f'{it.title} завершить до {it.dateTime}'
                for it in self.scheduledDeadlines
            ]
            res = 'Рекомендую следовать следующему расписанию:\n\n' + '\n\n'.join(user_message)
        else:
            res = ''

        if self.unscheduledDeadlines:
            user_message = [
                f'{it.title} (дедлайн {it.dateTime})'
                for it in self.unscheduledDeadlines
            ]
            res += '\n\nСледующие задачи были отброшены так как успеть до дедлайна невозможно:\n\n' \
                   + '\n\n'.join(user_message)

        if not res:
            return 'дедлайнов нет'
        return res
