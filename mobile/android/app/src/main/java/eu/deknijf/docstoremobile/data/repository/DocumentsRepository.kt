package eu.deknijf.docstoremobile.data.repository

import eu.deknijf.docstoremobile.data.api.DocstoreApi
import eu.deknijf.docstoremobile.data.model.DocumentDto

class DocumentsRepository(private val api: DocstoreApi) {
    suspend fun listDocuments(token: String, limit: Int = 100, offset: Int = 0): List<DocumentDto> {
        return api.listDocuments("Bearer $token", limit = limit, offset = offset)
    }

    suspend fun getDocument(token: String, documentId: String): DocumentDto {
        return api.getDocument("Bearer $token", documentId)
    }
}
