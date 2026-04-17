from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.types import Message

from timeline_hub.handlers.clips.ingest import try_dispatch_clip_intake
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

    async def send_clip_action_selection() -> None:
        handled = await try_dispatch_clip_intake(
            message=message,
            services=services,
            settings=settings,
        )
        if not handled:
            services.chat_message_buffer.flush(chat_id)

    services.task_scheduler.schedule(
        send_clip_action_selection,
        key=chat_id,
        delay=settings.forward_batch_timeout,
    )
