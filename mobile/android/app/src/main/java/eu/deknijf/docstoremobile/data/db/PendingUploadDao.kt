package eu.deknijf.docstoremobile.data.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import eu.deknijf.docstoremobile.data.model.UploadStatus
import kotlinx.coroutines.flow.Flow

@Dao
interface PendingUploadDao {
    @Query("SELECT * FROM pending_uploads ORDER BY createdAt DESC")
    fun observeAll(): Flow<List<PendingUploadEntity>>

    @Query("SELECT * FROM pending_uploads WHERE status IN ('PENDING','FAILED') ORDER BY createdAt ASC")
    suspend fun loadPendingForUpload(): List<PendingUploadEntity>

    @Query("SELECT COUNT(*) FROM pending_uploads WHERE status = 'PENDING'")
    fun observePendingCount(): Flow<Int>

    @Query("SELECT COUNT(*) FROM pending_uploads WHERE status = 'FAILED'")
    fun observeFailedCount(): Flow<Int>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(entity: PendingUploadEntity)

    @Update
    suspend fun update(entity: PendingUploadEntity)

    @Query("UPDATE pending_uploads SET status = :status, lastError = :error, updatedAt = :updatedAt, attemptCount = :attemptCount WHERE id = :id")
    suspend fun updateStatus(id: String, status: UploadStatus, error: String?, updatedAt: Long, attemptCount: Int)

    @Query("UPDATE pending_uploads SET status = :status, serverDocumentId = :serverDocumentId, updatedAt = :updatedAt, lastError = NULL WHERE id = :id")
    suspend fun markComplete(id: String, status: UploadStatus, serverDocumentId: String?, updatedAt: Long)

    @Query("DELETE FROM pending_uploads WHERE id = :id")
    suspend fun deleteById(id: String)
}
