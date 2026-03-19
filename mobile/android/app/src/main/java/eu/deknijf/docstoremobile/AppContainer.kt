package eu.deknijf.docstoremobile

import android.content.Context
import eu.deknijf.docstoremobile.data.api.NetworkModule
import eu.deknijf.docstoremobile.data.api.SessionStore
import eu.deknijf.docstoremobile.data.db.AppDatabase
import eu.deknijf.docstoremobile.data.repository.AuthRepository
import eu.deknijf.docstoremobile.data.repository.DocumentsRepository
import eu.deknijf.docstoremobile.data.repository.UploadQueueRepository

class AppContainer(context: Context) {
    private val appContext = context.applicationContext
    private val database = AppDatabase.get(appContext)

    val sessionStore = SessionStore(appContext)
    val authRepository = AuthRepository(NetworkModule.api, sessionStore)
    val documentsRepository = DocumentsRepository(NetworkModule.api)
    val uploadQueueRepository = UploadQueueRepository(appContext, NetworkModule.api, database.pendingUploadDao())
}
