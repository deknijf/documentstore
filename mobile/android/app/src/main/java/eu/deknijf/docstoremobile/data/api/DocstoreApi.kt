package eu.deknijf.docstoremobile.data.api

import eu.deknijf.docstoremobile.data.model.AuthResponse
import eu.deknijf.docstoremobile.data.model.DocumentDto
import eu.deknijf.docstoremobile.data.model.LoginRequest
import eu.deknijf.docstoremobile.data.model.UserDto
import okhttp3.MultipartBody
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part
import retrofit2.http.Path
import retrofit2.http.Query

interface DocstoreApi {
    @POST("api/auth/login")
    suspend fun login(@Body payload: LoginRequest): AuthResponse

    @GET("api/auth/me")
    suspend fun me(@Header("Authorization") authorization: String): UserDto

    @GET("api/documents")
    suspend fun listDocuments(
        @Header("Authorization") authorization: String,
        @Query("limit") limit: Int = 100,
        @Query("offset") offset: Int = 0,
    ): List<DocumentDto>

    @GET("api/documents/{documentId}")
    suspend fun getDocument(
        @Header("Authorization") authorization: String,
        @Path("documentId") documentId: String,
    ): DocumentDto

    @Multipart
    @POST("api/documents")
    suspend fun uploadDocument(
        @Header("Authorization") authorization: String,
        @Part file: MultipartBody.Part,
    ): DocumentDto
}
