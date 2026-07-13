from ssq_analyzer.models import Ticket


LONG_TERM_FIXED_TICKET = Ticket(red=(2, 5, 10, 25, 26, 31), blue=16)


def with_long_term_fixed_first(tickets: list[Ticket]) -> list[Ticket]:
    return [LONG_TERM_FIXED_TICKET, *tickets[1:]]
