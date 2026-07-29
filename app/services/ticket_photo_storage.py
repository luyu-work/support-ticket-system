"""Save ticket photos to local disk."""

import re
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.settings import ApplicationSettings, get_application_settings
from app.models import MAX_ATTACHMENTS_PER_TICKET

ALLOWED_PHOTO_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
}


class TooManyTicketPhotosError(Exception):
    def __init__(self, photo_count: int) -> None:
        self.photo_count = photo_count
        super().__init__(f"Too many photos: {photo_count}")


class InvalidTicketPhotoError(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


def _safe_file_name(original_file_name: str) -> str:
    cleaned = Path(original_file_name).name
    cleaned = re.sub(r"[^\w.\-]+", "_", cleaned, flags=re.UNICODE)
    return cleaned[:180] or "photo.bin"


def get_ticket_uploads_root(settings: ApplicationSettings | None = None) -> Path:
    application_settings = settings or get_application_settings()
    uploads_root = Path(application_settings.ticket_uploads_directory)
    if not uploads_root.is_absolute():
        uploads_root = Path.cwd() / uploads_root
    uploads_root.mkdir(parents=True, exist_ok=True)
    return uploads_root


def validate_ticket_photos(
    photo_files: list[UploadFile],
    settings: ApplicationSettings | None = None,
) -> None:
    application_settings = settings or get_application_settings()
    if len(photo_files) > MAX_ATTACHMENTS_PER_TICKET:
        raise TooManyTicketPhotosError(len(photo_files))

    for photo_file in photo_files:
        content_type = (photo_file.content_type or "").lower()
        if content_type not in ALLOWED_PHOTO_CONTENT_TYPES:
            raise InvalidTicketPhotoError(
                f"File type not allowed: {photo_file.filename or 'unknown'}"
            )


def save_ticket_photo_to_disk(
    *,
    support_ticket_id: int,
    photo_file: UploadFile,
    settings: ApplicationSettings | None = None,
) -> tuple[str, str]:
    """
    Save one photo. Returns (storage_path relative string, original_file_name).
    """
    application_settings = settings or get_application_settings()
    original_file_name = photo_file.filename or "photo.bin"
    safe_name = _safe_file_name(original_file_name)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"

    ticket_folder = get_ticket_uploads_root(application_settings) / str(support_ticket_id)
    ticket_folder.mkdir(parents=True, exist_ok=True)
    destination_path = ticket_folder / unique_name

    bytes_written = 0
    max_size = application_settings.max_ticket_photo_size_bytes
    with destination_path.open("wb") as output_file:
        while True:
            chunk = photo_file.file.read(1024 * 64)
            if not chunk:
                break
            bytes_written += len(chunk)
            if bytes_written > max_size:
                output_file.close()
                destination_path.unlink(missing_ok=True)
                raise InvalidTicketPhotoError(
                    f"File too large (max {max_size} bytes): {original_file_name}"
                )
            output_file.write(chunk)

    # Store path relative to project for portability
    relative_storage_path = str(
        Path(application_settings.ticket_uploads_directory)
        / str(support_ticket_id)
        / unique_name
    ).replace("\\", "/")
    return relative_storage_path, original_file_name
