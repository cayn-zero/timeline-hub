from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.types import Message

from timeline_hub.handlers.clips.ingest import try_dispatch_clip_intake
from timeline_hub.handlers.tracks.ingest import try_dispatch_track_intake
from timeline_hub.services.container import Services
from timeline_hub.settings import Settings

router = Router()


@router.message(F.chat.type == ChatType.PRIVATE, F.text | F.photo | F.audio | F.video)
async def on_buffered_relevant_message(
    message: Message,
    services: Services,
    settings: Settings,
) -> None:
    chat_id = message.chat.id
    services.chat_message_buffer.append(message, chat_id=chat_id)

    async def send_action_selection() -> None:
        ordered_buffered_messages = services.chat_message_buffer.peek_flat(chat_id)
        has_photo = any(buffered_message.photo is not None for buffered_message in ordered_buffered_messages)
        has_audio = any(buffered_message.audio is not None for buffered_message in ordered_buffered_messages)
        has_video = any(
            buffered_message.video is not None or getattr(buffered_message, 'animation', None) is not None
            for buffered_message in ordered_buffered_messages
        )
        first_photo_index = next(
            (
                index
                for index, buffered_message in enumerate(ordered_buffered_messages)
                if buffered_message.photo is not None
            ),
            None,
        )
        first_audio_index = next(
            (
                index
                for index, buffered_message in enumerate(ordered_buffered_messages)
                if buffered_message.audio is not None
            ),
            None,
        )

        if has_video and not has_photo and not has_audio:
            handled = await try_dispatch_clip_intake(
                message=message,
                services=services,
                settings=settings,
            )
        elif (
            has_photo
            and has_audio
            and not has_video
            and first_photo_index is not None
            and first_audio_index is not None
            and first_photo_index < first_audio_index
        ):
            handled = await try_dispatch_track_intake(
                message=message,
                services=services,
                settings=settings,
            )
        else:
            handled = False

        if not handled:
            services.chat_message_buffer.flush(chat_id)
            await message.answer(text="Can't dispatch")

    services.task_scheduler.schedule(
        send_action_selection,
        key=chat_id,
        delay=settings.forward_batch_timeout,
    )
