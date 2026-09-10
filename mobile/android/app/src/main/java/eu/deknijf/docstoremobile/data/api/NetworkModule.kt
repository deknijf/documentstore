package eu.deknijf.docstoremobile.data.api

import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import eu.deknijf.docstoremobile.BuildConfig
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import java.util.concurrent.TimeUnit

/**
 * Builds the API client. Takes a callback so a rejected session can be dropped
 * in one place instead of at every call site.
 */
class NetworkModule(onUnauthorized: () -> Unit) {
    private val json = Json {
        ignoreUnknownKeys = true
        explicitNulls = false
        isLenient = true
    }

    private val client: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(120, TimeUnit.SECONDS)
        .writeTimeout(120, TimeUnit.SECONDS)
        .addInterceptor(UnauthorizedInterceptor(onUnauthorized))
        .addInterceptor(HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.BASIC })
        .build()

    val api: DocstoreApi = Retrofit.Builder()
        .baseUrl(BuildConfig.DOCSTORE_BASE_URL)
        .client(client)
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .build()
        .create(DocstoreApi::class.java)
}
