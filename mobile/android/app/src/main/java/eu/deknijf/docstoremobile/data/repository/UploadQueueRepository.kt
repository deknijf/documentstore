package eu.deknijf.docstoremobile.data.repository

import android.content.Context
import android.net.Uri
import eu.deknijf.docstoremobile.data.api.DocstoreApi
import eu.deknijf.docstoremobile.data.db.PendingUploadDao
import eu.deknijf.docstoremobile.data.db.PendingUploadEntity
import eu.deknijf.docstoremobile.data.model.QueueSummary
import eu.deknijf.docstoremobile.data.model.UploadStatus
import eu.deknijf.docstoremobile.util.FileUtils
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File
import java.util.UUID

class UploadQueueRepository(
    private val context: Context,
    private val api: DocstoreApi,
    private val dao: PendingUploadDao,
) {
    fun observeQueue(): Flow<List<PendingUploadEntity>> = dao.observeAll()

    fun observeSummary(): Flow<QueueSummary> = combine(
        dao.observePendingCount(),
        dao.observeFailedCount(),
    ) { pending, failed ->
        QueueSummary(pendingCount = pending, failedCount = failed)
    }

    suspend fun enqueueScan(uri: Uri, displayNameHint: String? = null, mimeTypeHint: String? = null): PendingUploadEntity {
        val copied = FileUtils.copyUriToAppStorage(context, uri, fallbackExtension = "pdf")
        return enqueuePreparedFile(
            file = copied,
            displayNameHint = displayNameHint,
            mimeTypeHint = mimeTypeHint,
        )
    }

    suspend fun enqueuePreparedFile(
        file: File,
        displayNameHint: String? = null,
        mimeTypeHint: String? = null,
    ): PendingUploadEntity {
        val now = System.currentTimeMillis()
        val entity = PendingUploadEntity(
            id = UUID.randomUUID().toString(),
            localPath = file.absolutePath,
            displayName = displayNameHint?.takeIf { it.isNotBlank() } ?: file.name,
            mimeType = mimeTypeHint?.takeIf { it.isNotBlank() } ?: guessMimeType(file),
            createdAt = now,
            updatedAt = now,
            attemptCount = 0,
            status = UploadStatus.PENDING,
            lastError = null,
            serverDocumentId = null,
            sizeBytes = file.length(),
        )
        dao.insert(entity)
        return entity
    }

    suspend fun processPendingUploads(token: String): Result<Int> {
        return runCatching {
            var uploaded = 0
            dao.loadPendingForUpload().forEach { row ->
                val file = File(row.localPath)
                if (!file.exists()) {
                    dao.updateStatus(
                        id = row.id,
                        status = UploadStatus.FAILED,
                        error = "Bestand niet meer gevonden op toestel.",
                        updatedAt = System.currentTimeMillis(),
                        attemptCount = row.attemptCount + 1,
                    )
                    return@forEach
                }

                dao.updateStatus(
                    id = row.id,
                    status = UploadStatus.UPLOADING,
                    error = null,
                    updatedAt = System.currentTimeMillis(),
                    attemptCount = row.attemptCount,
                )

                runCatching {
                    val part = MultipartBody.Part.createFormData(
                        "file",
                        row.displayName,
                        file.asRequestBody(row.mimeType.toMediaTypeOrNull()),
                    )
                    api.uploadDocument("Bearer $token", part)
                }.onSuccess { document ->
                    dao.markComplete(
                        id = row.id,
                        status = UploadStatus.COMPLETE,
                        serverDocumentId = document.id,
                        updatedAt = System.currentTimeMillis(),
                    )
                    file.delete()
                    uploaded += 1
                }.onFailure { ex ->
                    dao.updateStatus(
                        id = row.id,
                        status = UploadStatus.FAILED,
                        error = ex.message ?: "Upload mislukt",
                        updatedAt = System.currentTimeMillis(),
                        attemptCount = row.attemptCount + 1,
                    )
                }
            }
            uploaded
        }
    }

    suspend fun removeCompletedUpload(id: String) {
        dao.deleteById(id)
    }

    private fun guessMimeType(file: File): String {
        return when (file.extension.lowercase()) {
            "pdf" -> "application/pdf"
            "jpg", "jpeg" -> "image/jpeg"
            "png" -> "image/png"
            else -> "application/octet-stream"
        }
    }
}
