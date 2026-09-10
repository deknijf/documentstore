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

    /**
     * Rows the worker may still try. A permanently failing upload used to be
     * retried every fifteen minutes forever, because FAILED was selected with
     * no regard for how often it had already been attempted.
     */
    @Query(
        "SELECT * FROM pending_uploads " +
            "WHERE status = 'PENDING' OR (status = 'FAILED' AND attemptCount < :maxAttempts) " +
            "ORDER BY createdAt ASC"
    )
    suspend fun loadPendingForUpload(maxAttempts: Int): List<PendingUploadEntity>


    /** Puts every failed upload back in the queue, for the manual retry button. */
    @Query(
        "UPDATE pending_uploads SET status = 'PENDING', attemptCount = 0, lastError = NULL, " +
            "updatedAt = :updatedAt WHERE status = 'FAILED'"
    )
    suspend fun requeueFailed(updatedAt: Long): Int

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
