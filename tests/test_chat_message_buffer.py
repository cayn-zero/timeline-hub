from aiogram.types import Message

from timeline_hub.services.message_buffer import ChatMessageBuffer


def _message(message_id: int, *, chat_id: int, media_group_id: str | None = None) -> Message:
    return Message.model_validate(
        {
            'message_id': message_id,
            'date': 1_700_000_000,
            'chat': {'id': chat_id, 'type': 'private'},
            'media_group_id': media_group_id,
        }
    )


def test_flush_unknown_chat_returns_none_and_preserves_version() -> None:
    buffer = ChatMessageBuffer()

    assert buffer.peek_raw(100) == []
    assert buffer.flush(100) is None
    assert buffer.version(100) == 0


def test_append_and_peek_raw_returns_copy_without_mutating_internal_state() -> None:
    buffer = ChatMessageBuffer()
    first = _message(1, chat_id=100)
    second = _message(2, chat_id=100)

    buffer.append(first, chat_id=100)
    assert buffer.version(100) == 1
    buffer.append(second, chat_id=100)
    assert buffer.version(100) == 2

    peeked = buffer.peek_raw(100)
    assert peeked == [first, second]
    assert buffer.version(100) == 2

    peeked.clear()
    assert buffer.peek_raw(100) == [first, second]
    assert buffer.version(100) == 2


def test_peek_ordered_returns_messages_sorted_by_message_id() -> None:
    buffer = ChatMessageBuffer()
    third = _message(3, chat_id=100)
    first = _message(1, chat_id=100)
    second = _message(2, chat_id=100)

    buffer.append(third, chat_id=100)
    buffer.append(first, chat_id=100)
    buffer.append(second, chat_id=100)

    assert buffer.peek_flat(100) == [first, second, third]
    assert buffer.peek_raw(100) == [third, first, second]
    assert buffer.version(100) == 3


def test_flush_returns_all_messages_for_chat_and_clears_it() -> None:
    buffer = ChatMessageBuffer()
    first = _message(1, chat_id=100)
    second = _message(2, chat_id=100)

    buffer.append(first, chat_id=100)
    buffer.append(second, chat_id=100)

    assert buffer.peek_raw(100) == [first, second]
    assert buffer.flush(100) is None
    assert buffer.version(100) == 3
    assert buffer.peek_raw(100) == []
    assert buffer.flush(100) is None
    assert buffer.version(100) == 3


def test_chat_isolation_between_append_peek_and_flush() -> None:
    buffer = ChatMessageBuffer()
    a1 = _message(1, chat_id=100)
    a2 = _message(2, chat_id=100)
    b1 = _message(3, chat_id=200)

    buffer.append(a1, chat_id=100)
    buffer.append(b1, chat_id=200)
    buffer.append(a2, chat_id=100)

    assert buffer.peek_raw(100) == [a1, a2]
    assert buffer.peek_raw(200) == [b1]
    assert buffer.flush(100) is None
    assert buffer.peek_raw(200) == [b1]


def test_peek_grouped_orders_by_message_id_and_groups_by_media_group_id() -> None:
    buffer = ChatMessageBuffer()
    # Intentionally append out of order to verify grouping uses message_id ordering.
    m4 = _message(4, chat_id=100, media_group_id='g2')
    m2 = _message(2, chat_id=100, media_group_id='g1')
    m5 = _message(5, chat_id=100, media_group_id='g2')
    m1 = _message(1, chat_id=100)
    m3 = _message(3, chat_id=100, media_group_id='g1')

    for message in [m4, m2, m5, m1, m3]:
        buffer.append(message, chat_id=100)

    assert buffer.peek_grouped(100) == [
        (m1,),
        (m2, m3),
        (m4, m5),
    ]
    assert buffer.peek_raw(100) == [m4, m2, m5, m1, m3]
    assert buffer.flush(100) is None
    assert buffer.version(100) == 6


def test_explicit_grouping_after_flush_uses_requested_chat_only() -> None:
    buffer = ChatMessageBuffer()
    chat_a_2 = _message(2, chat_id=100, media_group_id='a')
    chat_b_1 = _message(1, chat_id=200, media_group_id='b')
    chat_a_1 = _message(1, chat_id=100, media_group_id='a')
    chat_b_2 = _message(2, chat_id=200, media_group_id='b')

    buffer.append(chat_a_2, chat_id=100)
    buffer.append(chat_b_1, chat_id=200)
    buffer.append(chat_a_1, chat_id=100)
    buffer.append(chat_b_2, chat_id=200)

    assert buffer.peek_grouped(100) == [(chat_a_1, chat_a_2)]
    assert buffer.peek_raw(100) == [chat_a_2, chat_a_1]
    assert buffer.flush(100) is None
    assert buffer.version(100) == 3
    assert buffer.peek_raw(200) == [chat_b_1, chat_b_2]
    assert buffer.version(200) == 2
    assert buffer.peek_grouped(200) == [(chat_b_1, chat_b_2)]
    assert buffer.peek_raw(200) == [chat_b_1, chat_b_2]
    assert buffer.flush(200) is None
    assert buffer.version(200) == 3


def test_append_duplicate_message_id_in_same_chat_ignores_duplicate_and_version_bumps_once() -> None:
    buffer = ChatMessageBuffer()
    first = _message(10, chat_id=100)
    duplicate = _message(10, chat_id=100)

    buffer.append(first, chat_id=100)
    buffer.append(duplicate, chat_id=100)

    assert buffer.peek_raw(100) == [first]
    assert buffer.version(100) == 1


def test_append_duplicate_message_id_in_same_chat_preserves_original_message() -> None:
    buffer = ChatMessageBuffer()
    original = _message(20, chat_id=100, media_group_id='g1')
    duplicate_different_content = _message(20, chat_id=100, media_group_id='g2')

    buffer.append(original, chat_id=100)
    buffer.append(duplicate_different_content, chat_id=100)

    assert buffer.peek_raw(100) == [original]
    assert buffer.peek_raw(100)[0].media_group_id == 'g1'
    assert buffer.version(100) == 1


def test_append_same_message_id_in_different_chats_is_independent() -> None:
    buffer = ChatMessageBuffer()
    chat_a = _message(30, chat_id=100)
    chat_b = _message(30, chat_id=200)

    buffer.append(chat_a, chat_id=100)
    buffer.append(chat_b, chat_id=200)

    assert buffer.peek_raw(100) == [chat_a]
    assert buffer.peek_raw(200) == [chat_b]
    assert buffer.version(100) == 1
    assert buffer.version(200) == 1


def test_peek_views_do_not_contain_duplicates_after_duplicate_append() -> None:
    buffer = ChatMessageBuffer()
    m2 = _message(2, chat_id=100, media_group_id='g')
    m1 = _message(1, chat_id=100, media_group_id='g')
    m2_duplicate = _message(2, chat_id=100, media_group_id='other')

    buffer.append(m2, chat_id=100)
    buffer.append(m1, chat_id=100)
    buffer.append(m2_duplicate, chat_id=100)

    assert buffer.peek_flat(100) == [m1, m2]
    assert buffer.peek_grouped(100) == [(m1, m2)]
    assert buffer.version(100) == 2


def test_duplicate_append_after_flush_is_allowed_and_bumps_version() -> None:
    buffer = ChatMessageBuffer()
    message = _message(40, chat_id=100)
    same_message_id_after_flush = _message(40, chat_id=100)

    buffer.append(message, chat_id=100)
    assert buffer.version(100) == 1
    assert buffer.flush(100) is None
    assert buffer.version(100) == 2

    buffer.append(same_message_id_after_flush, chat_id=100)
    assert buffer.peek_raw(100) == [same_message_id_after_flush]
    assert buffer.version(100) == 3
