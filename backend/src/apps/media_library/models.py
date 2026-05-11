from pathlib import Path

from django.conf import settings
from django.db import models


class MediaType(models.TextChoices):
    AUDIO = "audio", "Audio"
    VIDEO = "video", "Video"


class PlayerDisplayMode(models.TextChoices):
    UNIFORM = "uniform", "Uniform"
    ORIGINAL = "original", "Original"


class ExternalSourceProvider(models.TextChoices):
    DIRECT_LINK = "direct_link", "Direct Link"
    YOUTUBE = "youtube", "YouTube"
    PODCAST = "podcast", "Podcast"
    OTHER = "other", "Other"


class AssetOrigin(models.TextChoices):
    LOCAL_UPLOAD = "local_upload", "Local Upload"
    EXTERNAL_STREAM = "external_stream", "External Stream"


class MediaFormat(models.TextChoices):
    MP4 = "mp4", "MP4"
    WEBM = "webm", "WebM"
    MOV = "mov", "MOV"
    MKV = "mkv", "MKV"
    MP3 = "mp3", "MP3"
    M4A = "m4a", "M4A"
    AAC = "aac", "AAC"
    WAV = "wav", "WAV"
    FLAC = "flac", "FLAC"
    OTHER = "other", "Other"


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimestampedModel):
    name = models.CharField(max_length=120)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_categories",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "name"],
                name="unique_category_name_per_parent",
            )
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Tag(TimestampedModel):
    name = models.CharField(max_length=80, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_tags",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ExternalSource(TimestampedModel):
    provider = models.CharField(
        max_length=32,
        choices=ExternalSourceProvider.choices,
        default=ExternalSourceProvider.OTHER,
    )
    source_url = models.URLField()
    external_id = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=255, blank=True)
    author_name = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_external_sources",
    )

    class Meta:
        ordering = ["provider", "title", "source_url"]

    def __str__(self) -> str:
        return self.title or self.source_url


class MediaAsset(TimestampedModel):
    origin = models.CharField(
        max_length=32,
        choices=AssetOrigin.choices,
        default=AssetOrigin.LOCAL_UPLOAD,
    )
    file_format = models.CharField(
        max_length=16,
        choices=MediaFormat.choices,
        default=MediaFormat.OTHER,
    )
    uploaded_file = models.FileField(upload_to="media_assets/", null=True, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)
    storage_path = models.CharField(max_length=500)
    file_size_bytes = models.PositiveBigIntegerField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_media_assets",
    )

    @property
    def asset_url(self) -> str:
        if self.uploaded_file:
            return self.uploaded_file.url
        return self.storage_path

    @property
    def filename(self) -> str:
        if self.uploaded_file:
            return Path(self.uploaded_file.name).name
        return Path(self.storage_path).name

    def __str__(self) -> str:
        return self.storage_path


class MediaItem(TimestampedModel):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    media_type = models.CharField(max_length=16, choices=MediaType.choices)
    player_display_mode = models.CharField(
        max_length=16,
        choices=PlayerDisplayMode.choices,
        default=PlayerDisplayMode.UNIFORM,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_media_items",
    )
    categories = models.ManyToManyField(Category, blank=True, related_name="media_items")
    tags = models.ManyToManyField(Tag, blank=True, related_name="media_items")
    asset = models.ForeignKey(
        MediaAsset,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="media_items",
    )
    external_source = models.ForeignKey(
        ExternalSource,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="media_items",
    )
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title
