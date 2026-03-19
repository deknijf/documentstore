package eu.deknijf.docstoremobile.data.db

import androidx.room.Entity
import androidx.room.PrimaryKey
import eu.deknijf.docstoremobile.data.model.UploadStatus

@Entity(tableName = "pending_uploads")
data class PendingUploadEntity(
    @PrimaryKey val id: String,
    val localPath: String,
    val displayName: String,
    val mimeType: String,
    val createdAt: Long,
    val updatedAt: Long,
    val attemptCount: Int,
    val status: UploadStatus,
    val lastError: String?,
    val serverDocumentId: String?,
    val sizeBytes: Long,
)
