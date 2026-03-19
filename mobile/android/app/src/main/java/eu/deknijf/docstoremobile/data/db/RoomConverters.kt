package eu.deknijf.docstoremobile.data.db

import androidx.room.TypeConverter
import eu.deknijf.docstoremobile.data.model.UploadStatus

class RoomConverters {
    @TypeConverter
    fun toUploadStatus(value: String?): UploadStatus {
        return runCatching { UploadStatus.valueOf(value ?: UploadStatus.PENDING.name) }
            .getOrDefault(UploadStatus.PENDING)
    }

    @TypeConverter
    fun fromUploadStatus(value: UploadStatus?): String {
        return (value ?: UploadStatus.PENDING).name
    }
}
